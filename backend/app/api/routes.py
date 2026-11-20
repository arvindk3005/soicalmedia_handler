from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from pypdf import PdfReader
from ..api.deps import current_user
from ..core.config import get_settings
from ..core.security import hash_password, issue_token, verify_password
from ..db import mongodb
from ..schemas.contracts import AnalyzeRequest, AnalysisResponse, LoginRequest, PostCreate, RegisterRequest, TokenResponse
from ..services.provider import analyze_content

router = APIRouter(prefix="/api")

@router.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "service": "pulsepilot",
        "default_provider": settings.ai_provider,
        "ollama_base_url": settings.ollama_base_url,
        "gemini_configured": bool(settings.gemini_api_key.strip())
    }

@router.post("/auth/register", response_model=TokenResponse)
def register(body: RegisterRequest):
    user_id = mongodb.create_user(body.name, body.email.lower(), hash_password(body.password))
    if not user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    return TokenResponse(access_token=issue_token(user_id))

@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = mongodb.get_user_by_email(body.email.lower())
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    # Fix: issue JWT token with user id, instead of raw ObjectId string
    return TokenResponse(access_token=issue_token(str(user["_id"])))

@router.get("/posts")
def list_posts(user_id: str = Depends(current_user)):
    return mongodb.list_posts(user_id)

@router.post("/posts")
def create_post(body: PostCreate, user_id: str = Depends(current_user)):
    post_id = mongodb.create_post(user_id, body.model_dump())
    return {"id": post_id, **body.model_dump()}

@router.get("/queries")
def list_queries(user_id: str = Depends(current_user)):
    """Retrieve the user's history of AI queries and recommendations."""
    return mongodb.list_queries(user_id)

@router.post("/uploads")
async def upload(file: UploadFile = File(...), user_id: str = Depends(current_user)):
    allowed = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Upload a PDF, JPEG, PNG or WebP image")
    
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Maximum upload size is 10 MB")
    
    settings = get_settings()
    folder = Path(settings.upload_dir) / user_id
    folder.mkdir(parents=True, exist_ok=True)
    
    safe_filename = Path(file.filename or "upload").name
    file_path = folder / f"{uuid4()}-{safe_filename}"
    file_path.write_bytes(content)
    
    extracted = ""
    if file.content_type == "application/pdf":
        try:
            reader = PdfReader(str(file_path))
            extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            extracted = ""
    
    attachment_id = mongodb.save_attachment(
        user_id=user_id,
        filename=safe_filename,
        content_type=file.content_type,
        path=str(file_path),
        extracted_text=extracted
    )
    
    return {
        "id": attachment_id,
        "filename": safe_filename,
        "content_type": file.content_type
    }

@router.post("/analysis", response_model=AnalysisResponse)
def analysis(body: AnalyzeRequest, user_id: str = Depends(current_user)):
    attachment = None
    if body.attachment_id:
        attachment = mongodb.get_attachment(user_id, body.attachment_id)
        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    
    # Analyze draft content with chosen AI provider (Gemini or Ollama)
    result = analyze_content(
        content=body.content,
        platform=body.platform,
        attachment=attachment,
        provider=body.provider,
        model=body.model,
        target_audience=body.target_audience,
        goal=body.goal,
    )
    
    # Save the query and analysis result to MongoDB
    query_id = mongodb.save_query(
        user_id=user_id,
        content=body.content,
        platform=body.platform,
        provider=result.get("provider", "unknown"),
        model=result.get("model", ""),
        analysis_result=result,
        attachment_id=body.attachment_id
    )
    result["id"] = query_id
    return result
