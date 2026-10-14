import json
from parsers.api import now_iso


def parse(payload: dict) -> dict:
    cloud = payload.get("cloud") or {}
    raw = payload.get("raw") or {}
    name = payload.get("event_type") or raw.get("eventName")
    action = payload.get("action")
    if not action and name:
        if name.startswith("Create"):
            action = "create"
        elif name.startswith("Delete"):
            action = "delete"
        elif name == "ConsoleLogin":
            action = "login"
    return {
        "@timestamp": payload.get("@timestamp") or now_iso(),
        "tenant": payload["tenant"],
        "source": "aws",
        "vendor": "amazon",
        "product": "cloudtrail",
        "event_type": name,
        "action": action,
        "user": payload.get("user"),
        "src_ip": payload.get("ip") or raw.get("sourceIPAddress"),
        "cloud": {
            "account_id": cloud.get("account_id"),
            "region": cloud.get("region"),
            "service": cloud.get("service"),
        },
        "raw": json.dumps(payload, ensure_ascii=False),
        "_tags": ["cloud"],
    }