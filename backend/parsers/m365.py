import json
from parsers.api import now_iso


def parse(payload: dict) -> dict:
    status = payload.get("status")
    name = payload.get("event_type")
    return {
        "@timestamp": payload.get("@timestamp") or now_iso(),
        "tenant": payload["tenant"],
        "source": "m365",
        "vendor": "microsoft",
        "product": "m365-audit",
        "event_type": name,
        "event_subtype": payload.get("workload"),
        "action": "login" if name == "UserLoggedIn" else payload.get("action"),
        "user": payload.get("user"),
        "src_ip": payload.get("ip"),
        "severity": 3 if status and status.lower() != "success" else 1,
        "raw": json.dumps(payload, ensure_ascii=False),
        "_tags": ["saas"],
    }