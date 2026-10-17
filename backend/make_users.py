import json
import os

import bcrypt


def h(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


admin_pw = os.environ.get("ADMIN_PASSWORD", "admin123")
viewer_pw = os.environ.get("VIEWER_PASSWORD", "viewer123")

users = [
    {"username": "admin", "password_hash": h(admin_pw), "role": "admin", "tenants": ["*"]},
    {"username": "viewerA", "password_hash": h(viewer_pw), "role": "viewer", "tenants": ["demoa"]},
    {"username": "viewerB", "password_hash": h(viewer_pw), "role": "viewer", "tenants": ["demob"]},
]

with open("users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, indent=2)
print("users.json created")