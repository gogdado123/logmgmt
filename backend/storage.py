import os
from datetime import datetime, timezone
from opensearchpy import OpenSearch
from schema import INDEX_TEMPLATE

client = OpenSearch(os.environ.get("OPENSEARCH_URL", "http://opensearch:9200"))


def ensure_template():
    client.indices.put_index_template(name="logs-template", body=INDEX_TEMPLATE)


def index_name(tenant: str, ts: str) -> str:
    day = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y.%m.%d")
    return f"logs-{tenant.lower()}-{day}"


def save(doc: dict):
    idx = index_name(doc["tenant"], doc["@timestamp"])
    client.index(index=idx, body=doc, refresh=True)
    return idx