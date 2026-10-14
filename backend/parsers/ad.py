import json
from parsers.api import now_iso

EVENT_MAP = {
    4624: ("LogonSuccess", "login", 1),
    4625: ("LogonFailed", "login", 5),
}


def parse(payload: dict) -> dict:
    eid = payload.get("event_id")
    name, action, sev = EVENT_MAP.get(eid, (payload.get("event_type"), payload.get("action"), 3))
    return {
        "@timestamp": payload.get("@timestamp") or now_iso(),
        "tenant": payload["tenant"],
        "source": "ad",
        "vendor": "microsoft",
        "product": "windows-security",
        "event_type": payload.get("event_type") or name,
        "event_subtype": str(eid) if eid is not None else None,
        "action": action,
        "severity": sev,
        "user": payload.get("user"),
        "host": payload.get("host"),
        "src_ip": payload.get("ip"),
        "raw": json.dumps(payload, ensure_ascii=False),
        "_tags": ["windows"],
    }