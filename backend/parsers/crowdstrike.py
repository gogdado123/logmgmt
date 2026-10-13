import json
from parsers.api import now_iso


def parse(payload: dict) -> dict:
    return {
        "@timestamp": payload.get("@timestamp") or now_iso(),
        "tenant": payload["tenant"],
        "source": "crowdstrike",
        "vendor": "crowdstrike",
        "product": "falcon",
        "event_type": payload.get("event_type"),
        "host": payload.get("host"),
        "process": payload.get("process"),
        "severity": payload.get("severity"),
        "action": payload.get("action"),
        "raw": json.dumps(payload, ensure_ascii=False),
        "_tags": [],
    }