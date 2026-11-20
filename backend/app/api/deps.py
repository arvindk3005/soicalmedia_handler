from fastapi import Header, HTTPException
from ..core.security import read_token
def current_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401, "Missing bearer token")
    return read_token(authorization.removeprefix("Bearer "))
