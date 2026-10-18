import json
import os
import urllib.error
import urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost:8000")


def call(path, token=None):
    req = urllib.request.Request(BASE + path)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None


def login(user, pw):
    req = urllib.request.Request(
        BASE + "/auth/login",
        data=json.dumps({"username": user, "password": pw}).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req).read())["access_token"]


def test_viewer_cannot_read_other_tenant():
    token = login("viewerA", os.environ.get("VIEWER_PASSWORD", "viewer123"))
    status, _ = call("/search?tenant=demoB", token)
    assert status == 403


def test_search_requires_token():
    status, _ = call("/search")
    assert status == 401