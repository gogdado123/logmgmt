from fastapi import FastAPI, HTTPException, UploadFile, File
import json
from parsers import api, crowdstrike, firewall, network, aws, m365, ad
import storage

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


@app.post("/ingest")
def ingest(payload: dict):
    return {"indexed": process(payload)}


@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    try:
        data = json.loads(content)
        events = data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        # รองรับ NDJSON (หนึ่งบรรทัดต่อหนึ่ง event)
        events = [json.loads(l) for l in content.splitlines() if l.strip()]
    ok, failed = 0, []
    for i, ev in enumerate(events):
        try:
            process(ev)
            ok += 1
        except HTTPException as e:
            failed.append({"line": i, "error": e.detail})
    return {"total": len(events), "indexed": ok, "failed": failed}


@app.get("/search")
def search(tenant: str, q: str = "*", size: int = 20):
    body = {
        "size": size,
        "sort": [{"@timestamp": "desc"}],
        "query": {
            "bool": {
                "filter": [{"term": {"tenant": tenant.lower()}}],
                "must": [{"query_string": {"query": q}}],
            }
        },
    }
    res = storage.client.search(index=f"logs-{tenant.lower()}-*", body=body)
    return [h["_source"] for h in res["hits"]["hits"]]