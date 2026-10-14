from fastapi import FastAPI, HTTPException
from parsers import api, crowdstrike, firewall, network
import storage

app = FastAPI(title="Log Management Demo")

PARSERS = {
    "api": api.parse,
    "crowdstrike": crowdstrike.parse,
    "firewall": firewall.parse,
    "network": network.parse,
}


@app.on_event("startup")
def startup():
    storage.ensure_template()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(payload: dict):
    if "tenant" not in payload:
        raise HTTPException(status_code=400, detail="tenant is required")
    payload["tenant"] = payload["tenant"].lower()   # <-- เพิ่มบรรทัดนี้
    source = payload.get("source", "api")
    parser = PARSERS.get(source)
    if parser is None:
        raise HTTPException(status_code=400, detail=f"unsupported source: {source}")
    try:
        doc = parser(payload)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"parse error: {e}")
    idx = storage.save(doc)
    return {"indexed": idx}


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