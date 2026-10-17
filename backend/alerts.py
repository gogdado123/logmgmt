import asyncio
import os
from datetime import datetime, timedelta, timezone

import requests

import storage

THRESHOLD = int(os.environ.get("ALERT_THRESHOLD", "5"))
WINDOW_MIN = int(os.environ.get("ALERT_WINDOW_MIN", "5"))
WEBHOOK = os.environ.get("ALERT_WEBHOOK_URL", "")
FAILED_TYPES = ["app_login_failed", "LogonFailed"]
RULE_NAME = "repeated-login-failure"


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_index():
    if not storage.client.indices.exists(index="alerts"):
        storage.client.indices.create(
            index="alerts",
            body={"mappings": {"properties": {
                "@timestamp": {"type": "date"},
                "tenant": {"type": "keyword"},
                "rule": {"type": "keyword"},
                "src_ip": {"type": "ip"},
                "count": {"type": "integer"},
                "users": {"type": "keyword"},
                "message": {"type": "text"},
            }}},
        )


def already_alerted(tenant, ip, since):
    res = storage.client.search(index="alerts", body={
        "size": 0,
        "query": {"bool": {"filter": [
            {"term": {"tenant": tenant}},
            {"term": {"src_ip": ip}},
            {"range": {"@timestamp": {"gte": _iso(since)}}},
        ]}},
    })
    return res["hits"]["total"]["value"] > 0


def send_webhook(alert):
    if not WEBHOOK:
        return
    try:
        requests.post(WEBHOOK, json=alert, timeout=5)
    except requests.RequestException as e:
        print(f"webhook failed: {e}", flush=True)


def check_once():
    since = _now() - timedelta(minutes=WINDOW_MIN)
    body = {
        "size": 0,
        "query": {"bool": {"filter": [
            {"terms": {"event_type": FAILED_TYPES}},
            {"range": {"@timestamp": {"gte": _iso(since)}}},
            {"exists": {"field": "src_ip"}},
        ]}},
        "aggs": {"by_tenant": {"terms": {"field": "tenant", "size": 100}, "aggs": {
            "by_ip": {
                "terms": {"field": "src_ip", "size": 50, "min_doc_count": THRESHOLD},
                "aggs": {"users": {"terms": {"field": "user", "size": 10}}},
            }}}},
    }
    res = storage.client.search(index="logs-*", body=body, ignore_unavailable=True)
    created = 0
    for t in res["aggregations"]["by_tenant"]["buckets"]:
        for ip in t["by_ip"]["buckets"]:
            if already_alerted(t["key"], ip["key"], since):
                continue
            users = [u["key"] for u in ip["users"]["buckets"]]
            alert = {
                "@timestamp": _iso(_now()),
                "tenant": t["key"],
                "rule": RULE_NAME,
                "src_ip": ip["key"],
                "count": ip["doc_count"],
                "users": users,
                "message": f"{ip['doc_count']} failed logins from {ip['key']} within {WINDOW_MIN} min",
            }
            storage.client.index(index="alerts", body=alert, refresh=True)
            send_webhook(alert)
            created += 1
    return created


async def loop():
    while True:
        try:
            await asyncio.to_thread(check_once)
        except Exception as e:
            print(f"alert check failed: {e}", flush=True)
        await asyncio.sleep(30)