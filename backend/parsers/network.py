from parsers.firewall import HEADER, KV, parse_syslog_time


def parse(payload: dict) -> dict:
    line = payload["message"]
    m = HEADER.match(line.strip())
    if not m:
        raise ValueError("invalid syslog format")
    kv = dict(KV.findall(m.group("rest")))
    pri = int(m.group("pri"))
    return {
        "@timestamp": parse_syslog_time(m.group("ts")),
        "tenant": payload["tenant"],
        "source": "network",
        "event_type": kv.get("event", "network_event"),
        "event_subtype": kv.get("reason"),
        "severity": pri % 8,
        "host": m.group("host"),
        "raw": line,
        "_tags": ["syslog", "router"],
    }