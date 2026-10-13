from datetime import datetime, timezone
import json

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse(payload: dict) -> dict:
    return {
        "@timestamp": payload.get("@timestamp") or now_iso(),
        "tenant": payload["tenant"],
        "source": payload.get("source", "api"),
        "event_type": payload.get("event_type"),
        "user": payload.get("user"),
        "src_ip": payload.get("ip"),
        "severity": payload.get("severity"),
        "action": payload.get("action"),
        "raw": json.dumps(payload, ensure_ascii=False),
        "_tags": [],
    }