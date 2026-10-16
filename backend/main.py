import json

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

import auth
import storage
from parsers import ad, api, aws, crowdstrike, firewall, m365, network

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
def startup():
    storage.ensure_template()


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


# ---------- Search ----------
@app.get("/search")
def search(
    q: str = "*",
    size: int = 20,
    tenant: str | None = None,
    user: dict = Depends(auth.current_user),
):
    if tenant:
        tenants = [auth.check_tenant(user, tenant)]
    elif "*" in user["tenants"]:
        tenants = None
    else:
        tenants = user["tenants"]

    filters = []
    if tenants is not None:
        filters.append({"terms": {"tenant": tenants}})
    body = {
        "size": min(size, 200),
        "sort": [{"@timestamp": "desc"}],
        "query": {"bool": {"filter": filters, "must": [{"query_string": {"query": q}}]}},
    }
    index = "logs-*" if tenants is None else ",".join(f"logs-{t}-*" for t in tenants)
    res = storage.client.search(index=index, body=body, ignore_unavailable=True)
    return [h["_source"] for h in res["hits"]["hits"]]