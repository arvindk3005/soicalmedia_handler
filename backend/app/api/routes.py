from fastapi import APIRouter, Depends, HTTPException
from ..api.deps import current_user
from ..core.security import hash_password, issue_token, verify_password
from ..db.database import connection
from ..schemas.contracts import AnalyzeRequest, LoginRequest, PostCreate, RegisterRequest, TokenResponse
from ..services.provider import analyze_content

router = APIRouter(prefix="/api")
@router.get("/health")
def health(): return {"status": "ok", "service": "pulsepilot"}
@router.post("/auth/register", response_model=TokenResponse)
def register(body: RegisterRequest):
    try:
        with connection() as db:
            cursor = db.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)", (body.name, body.email.lower(), hash_password(body.password))); db.commit()
            return TokenResponse(access_token=issue_token(cursor.lastrowid))
    except Exception: raise HTTPException(409, "An account with this email already exists")
@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    with connection() as db: user = db.execute("SELECT * FROM users WHERE email=?", (body.email.lower(),)).fetchone()
    if not user or not verify_password(body.password, user["password_hash"]): raise HTTPException(401, "Incorrect email or password")
    return TokenResponse(access_token=issue_token(user["id"]))
@router.get("/posts")
def list_posts(user_id: int = Depends(current_user)):
    with connection() as db: return [dict(row) for row in db.execute("SELECT * FROM posts WHERE user_id=? ORDER BY id DESC", (user_id,))]
@router.post("/posts")
def create_post(body: PostCreate, user_id: int = Depends(current_user)):
    with connection() as db:
        cursor = db.execute("INSERT INTO posts(user_id,content,platform,impressions,engagement) VALUES(?,?,?,?,?)", (user_id, body.content, body.platform, body.impressions, body.engagement)); db.commit()
    return {"id": cursor.lastrowid, **body.model_dump()}
@router.post("/analysis")
def analysis(body: AnalyzeRequest, user_id: int = Depends(current_user)): return analyze_content(body.content, body.platform)
