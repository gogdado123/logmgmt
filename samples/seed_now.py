import json
import urllib.request
from datetime import datetime, timedelta, timezone
import os
URL = os.environ.get("INGEST_URL", "http://localhost:8000/ingest")
KEY = os.environ.get("INGEST_API_KEY", "dev-ingest-key")


def post(doc):
    req = urllib.request.Request(
        URL, data=json.dumps(doc).encode(),
        headers={"Content-Type": "application/json", "X-API-Key": KEY},
    )
    urllib.request.urlopen(req).read()


def ts(minutes_ago):
    t = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


# login ล้มเหลวซ้ำจาก IP เดียว (ใช้ทดสอบ Alert วันที่ 8)
for i in range(8):
    post({"tenant": "demoA", "source": "api", "event_type": "app_login_failed",
          "user": "alice", "ip": "203.0.113.7", "@timestamp": ts(i)})

for i, u in enumerate(["bob", "carol", "dave", "alice"]):
    post({"tenant": "demoA", "source": "api", "event_type": "app_login_ok",
          "user": u, "ip": f"198.51.100.{10 + i}", "@timestamp": ts(20 + i * 30)})

post({"tenant": "demoA", "source": "crowdstrike", "event_type": "malware_detected",
      "host": "WIN10-01", "process": "powershell.exe", "severity": 8,
      "action": "quarantine", "@timestamp": ts(15)})

post({"tenant": "demoB", "source": "m365", "event_type": "UserLoggedIn",
      "user": "bob@demo.local", "ip": "198.51.100.23", "status": "Success",
      "workload": "Exchange", "@timestamp": ts(40)})

post({"tenant": "demoB", "source": "aws", "event_type": "CreateUser", "user": "admin",
      "cloud": {"service": "iam", "account_id": "123456789012", "region": "ap-southeast-1"},
      "@timestamp": ts(90)})

print("seeded")