import json
import bcrypt


def h(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


users = [
    {"username": "admin", "password_hash": h("admin123"), "role": "admin", "tenants": ["*"]},
    {"username": "viewerA", "password_hash": h("viewer123"), "role": "viewer", "tenants": ["demoa"]},
    {"username": "viewerB", "password_hash": h("viewer123"), "role": "viewer", "tenants": ["demob"]},
]

with open("users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, indent=2)
print("users.json created")