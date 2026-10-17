import json
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
import auth
import storage
from parsers import ad, api, aws, crowdstrike, firewall, m365, network
import asyncio
import alerts
import retention 

app = FastAPI(title="Log Management Demo")

PARSERS = {
    "api": api.parse,
    "crowdstrike": crowdstrike.parse,
    "firewall": firewall.parse,
    "network": network.parse,
    "aws": aws.parse,
    "m365": m365.parse,
    "ad": ad.parse,
}


@app.on_event("startup")
async def startup():
    storage.ensure_template()
    alerts.ensure_index()
    asyncio.create_task(alerts.loop())
    asyncio.create_task(retention.loop())


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Auth ----------
class LoginReq(BaseModel):
    username: str
    password: str


@app.post("/auth/login")
def login(req: LoginReq):
    user = auth.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {
        "access_token": auth.create_token(user),
        "token_type": "bearer",
        "role": user["role"],
        "tenants": user["tenants"],
    }


@app.get("/me")
def me(user: dict = Depends(auth.current_user)):
    return {"username": user["sub"], "role": user["role"], "tenants": user["tenants"]}


# ---------- Ingest ----------
def process(payload: dict) -> str:
    if "tenant" not in payload:
        raise HTTPException(status_code=400, detail="tenant is required")
    payload["tenant"] = payload["tenant"].lower()
    source = payload.get("source", "api")
    parser = PARSERS.get(source)
    if parser is None:
        raise HTTPException(status_code=400, detail=f"unsupported source: {source}")
    try:
        doc = parser(payload)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"parse error: {e}")
    return storage.save(doc)


@app.post("/ingest", dependencies=[Depends(auth.require_ingest_key)])
def ingest(payload: dict):
    return {"indexed": process(payload)}


@app.post("/ingest/file", dependencies=[Depends(auth.require_ingest_key)])
async def ingest_file(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    try:
        data = json.loads(content)
        events = data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        events = [json.loads(l) for l in content.splitlines() if l.strip()]
    ok, failed = 0, []
    for i, ev in enumerate(events):
        try:
            process(ev)
            ok += 1
        except HTTPException as e:
            failed.append({"line": i, "error": e.detail})
    return {"total": len(events), "indexed": ok, "failed": failed}

TOP_FIELDS = {"src_ip", "dst_ip", "user", "host", "event_type", "source", "action", "tenant"}


def build_query(user, q, tenant, source, start, end):
    if tenant:
        tenants = [auth.check_tenant(user, tenant)]
    elif "*" in user["tenants"]:
        tenants = None
    else:
        tenants = user["tenants"]

    filters = []
    if tenants is not None:
        filters.append({"terms": {"tenant": tenants}})
    if source:
        filters.append({"term": {"source": source}})
    if start or end:
        rng = {}
        if start:
            rng["gte"] = start
        if end:
            rng["lte"] = end
        filters.append({"range": {"@timestamp": rng}})

    query = {"bool": {"filter": filters, "must": [{"query_string": {"query": q}}]}}
    index = "logs-*" if tenants is None else ",".join(f"logs-{t}-*" for t in tenants)
    return index, query
# ---------- Search ----------
@app.get("/search")
def search(
    q: str = "*",
    size: int = 50,
    tenant: str | None = None,
    source: str | None = None,
    start: str | None = None,
    end: str | None = None,
    user: dict = Depends(auth.current_user),
):
    index, query = build_query(user, q, tenant, source, start, end)
    body = {"size": min(size, 200), "sort": [{"@timestamp": "desc"}], "query": query}
    try:
        res = storage.client.search(index=index, body=body, ignore_unavailable=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"bad query: {e}")
    return [h["_source"] for h in res["hits"]["hits"]]


@app.get("/stats/top")
def stats_top(
    field: str = "src_ip",
    n: int = 10,
    q: str = "*",
    tenant: str | None = None,
    source: str | None = None,
    start: str | None = None,
    end: str | None = None,
    user: dict = Depends(auth.current_user),
):
    if field not in TOP_FIELDS:
        raise HTTPException(status_code=400, detail=f"field must be one of {sorted(TOP_FIELDS)}")
    index, query = build_query(user, q, tenant, source, start, end)
    body = {
        "size": 0,
        "query": query,
        "aggs": {"top": {"terms": {"field": field, "size": min(n, 50)}}},
    }
    res = storage.client.search(index=index, body=body, ignore_unavailable=True)
    return [{"key": b["key"], "count": b["doc_count"]} for b in res["aggregations"]["top"]["buckets"]]


@app.get("/stats/timeline")
def stats_timeline(
    interval: str = "1h",
    q: str = "*",
    tenant: str | None = None,
    source: str | None = None,
    start: str | None = None,
    end: str | None = None,
    user: dict = Depends(auth.current_user),
):
    if interval not in {"1m", "5m", "15m", "1h", "1d"}:
        raise HTTPException(status_code=400, detail="interval must be 1m, 5m, 15m, 1h or 1d")
    index, query = build_query(user, q, tenant, source, start, end)
    body = {
        "size": 0,
        "query": query,
        "aggs": {"t": {"date_histogram": {"field": "@timestamp", "fixed_interval": interval}}},
    }
    res = storage.client.search(index=index, body=body, ignore_unavailable=True)
    return [
        {"time": b["key_as_string"], "count": b["doc_count"]}
        for b in res["aggregations"]["t"]["buckets"]
        if b["doc_count"] > 0
    ] 

# ---------- Alerts ----------
@app.get("/alerts")
def list_alerts(size: int = 50, user: dict = Depends(auth.current_user)):
    filters = []
    if "*" not in user["tenants"]:
        filters.append({"terms": {"tenant": user["tenants"]}})
    res = storage.client.search(index="alerts", body={
        "size": min(size, 200),
        "sort": [{"@timestamp": "desc"}],
        "query": {"bool": {"filter": filters}},
    })
    return [h["_source"] for h in res["hits"]["hits"]]


@app.post("/admin/retention/run")
def run_retention(user: dict = Depends(auth.require_admin)):
    return {"deleted": retention.purge_once()}


@app.post("/admin/alerts/check")
def run_alert_check(user: dict = Depends(auth.require_admin)):
    return {"created": alerts.check_once()}