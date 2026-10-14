import json
import re
from datetime import datetime, timezone

HEADER = re.compile(r"^<(?P<pri>\d+)>(?P<ts>\w{3}\s+\d+\s[\d:]{8})\s(?P<host>\S+)\s(?P<rest>.*)$")
KV = re.compile(r"(\w+)=(.*?)(?=\s\w+=|$)")


def parse_syslog_time(ts: str) -> str:
    # syslog ไม่มีปี ใช้ปีปัจจุบัน (UTC)
    year = datetime.now(timezone.utc).year
    dt = datetime.strptime(f"{year} {ts}", "%Y %b %d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


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
        "source": "firewall",
        "vendor": kv.get("vendor"),
        "product": kv.get("product"),
        "event_type": "firewall_" + kv.get("action", "event"),
        "action": kv.get("action"),
        "severity": pri % 8,
        "src_ip": kv.get("src"),
        "src_port": to_int(kv.get("spt")),
        "dst_ip": kv.get("dst"),
        "dst_port": to_int(kv.get("dpt")),
        "protocol": kv.get("proto"),
        "host": m.group("host"),
        "rule_name": kv.get("policy"),
        "raw": line,
        "_tags": ["syslog"],
    }