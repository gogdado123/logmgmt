import json
from datetime import datetime, timedelta, timezone


def ts(minutes_ago):
    t = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


events = [
    {"tenant": "demoB", "source": "aws",
     "cloud": {"service": "iam", "account_id": "123456789012", "region": "ap-southeast-1"},
     "event_type": "CreateUser", "user": "admin", "@timestamp": ts(3),
     "raw": {"eventName": "CreateUser", "requestParameters": {"userName": "temp-user"}}},
    {"tenant": "demoB", "source": "m365", "event_type": "UserLoggedIn",
     "user": "bob@demo.local", "ip": "198.51.100.23", "status": "Success",
     "workload": "Exchange", "@timestamp": ts(2)},
    {"tenant": "demoA", "source": "ad", "event_id": 4625, "event_type": "LogonFailed",
     "user": "demo\\eve", "host": "DC01", "ip": "203.0.113.77", "logon_type": 3,
     "@timestamp": ts(1)},
]

with open("samples/batch_now.json", "w", encoding="utf-8") as f:
    json.dump(events, f, indent=2)
print("samples/batch_now.json created")