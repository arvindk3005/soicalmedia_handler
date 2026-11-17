import base64, hashlib, hmac, json, secrets, time
from fastapi import HTTPException, status
from .config import get_settings

def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return f"{salt}${digest}"

def verify_password(password: str, encoded: str) -> bool:
    salt, digest = encoded.split("$", 1)
    return hmac.compare_digest(hash_password(password, salt), encoded)

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def issue_token(user_id: int) -> str:
    payload = _b64(json.dumps({"sub": user_id, "exp": int(time.time()) + 86400}).encode())
    signature = hmac.new(get_settings().jwt_secret.encode(), payload.encode(), hashlib.sha256).digest()
    return f"{payload}.{_b64(signature)}"

def read_token(token: str) -> int:
    try:
        payload, signature = token.split(".")
        expected = _b64(hmac.new(get_settings().jwt_secret.encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected): raise ValueError
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if data["exp"] < time.time(): raise ValueError
        return int(data["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
