import json
import os
import time
import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me")
JWT_ALG = "HS256"
TOKEN_TTL = 8 * 3600
USERS_FILE = os.environ.get("USERS_FILE", "users.json")
INGEST_API_KEY = os.environ.get("INGEST_API_KEY", "dev-ingest-key")

bearer = HTTPBearer(auto_error=False)


def load_users() -> dict:
    with open(USERS_FILE, encoding="utf-8") as f:
        return {u["username"]: u for u in json.load(f)}


def authenticate(username: str, password: str):
    user = load_users().get(username)
    if not user:
        return None
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return None
    return user


def create_token(user: dict) -> str:
    now = int(time.time())
    claims = {
        "sub": user["username"],
        "role": user["role"],
        "tenants": user["tenants"],
        "iat": now,
        "exp": now + TOKEN_TTL,
    }
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)


def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if cred is None:
        raise HTTPException(status_code=401, detail="missing token")
    try:
        return jwt.decode(cred.credentials, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid or expired token")


def require_admin(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return user


def allowed_tenants(user: dict) -> list:
    return user["tenants"]  # admin ใช้ ["*"] หมายถึงทุก tenant


def check_tenant(user: dict, tenant: str):
    tenant = tenant.lower()
    if "*" in user["tenants"] or tenant in user["tenants"]:
        return tenant
    raise HTTPException(status_code=403, detail="no access to this tenant")


def require_ingest_key(x_api_key: str = Header(default=None)):
    if x_api_key != INGEST_API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")