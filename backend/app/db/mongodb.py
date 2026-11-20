import logging
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from fastapi import HTTPException, status
from ..core.config import get_settings

logger = logging.getLogger("pulsepilot.db")

_client: MongoClient | None = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
        )
    return _client

def database():
    settings = get_settings()
    client = get_client()
    try:
        db = client[settings.mongodb_database]
        return db
    except PyMongoError as exc:
        logger.error(f"MongoDB connection error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: Could not connect to MongoDB at {settings.mongodb_url}. Please ensure MongoDB is running and MONGODB_URL is configured properly."
        )

def init_mongodb():
    """Initializes indexes and verifies MongoDB connectivity during startup."""
    settings = get_settings()
    try:
        client = get_client()
        client.admin.command("ping")
        db = client[settings.mongodb_database]
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.posts.create_index([("user_id", ASCENDING), ("created_at", -1)])
        db.queries.create_index([("user_id", ASCENDING), ("created_at", -1)])
        db.attachments.create_index([("user_id", ASCENDING)])
        logger.info(f"Connected to MongoDB database '{settings.mongodb_database}' successfully.")
    except Exception as exc:
        logger.warning(
            f"Could not connect to MongoDB at {settings.mongodb_url} during startup ({exc}). "
            "Database-dependent endpoints will return 503 until MongoDB is started."
        )

def serialize(document: dict | None) -> dict | None:
    if not document:
        return None
    doc = dict(document)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc

def create_user(name: str, email: str, password_hash: str) -> str | None:
    try:
        doc = {
            "name": name,
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc)
        }
        res = database().users.insert_one(doc)
        return str(res.inserted_id)
    except DuplicateKeyError:
        return None
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error while creating user. Check MongoDB connection."
        )

def get_user_by_email(email: str) -> dict | None:
    try:
        return database().users.find_one({"email": email.lower().strip()})
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error while retrieving user. Check MongoDB connection."
        )

def get_user_by_id(user_id: str) -> dict | None:
    try:
        return database().users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None

def create_post(user_id: str, payload: dict) -> str:
    try:
        doc = {
            **payload,
            "user_id": ObjectId(user_id),
            "created_at": datetime.now(timezone.utc)
        }
        res = database().posts.insert_one(doc)
        return str(res.inserted_id)
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error while saving post."
        )

def list_posts(user_id: str) -> list[dict]:
    try:
        rows = database().posts.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
        return [serialize(row) for row in rows]
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error while listing posts."
        )

def save_query(
    user_id: str,
    content: str,
    platform: str,
    provider: str,
    model: str,
    analysis_result: dict,
    attachment_id: str | None = None
) -> str:
    """Saves user query and AI analysis result into MongoDB."""
    try:
        doc = {
            "user_id": ObjectId(user_id),
            "content": content,
            "platform": platform,
            "provider": provider,
            "model": model,
            "attachment_id": ObjectId(attachment_id) if attachment_id else None,
            "analysis": analysis_result,
            "created_at": datetime.now(timezone.utc)
        }
        res = database().queries.insert_one(doc)
        return str(res.inserted_id)
    except PyMongoError as exc:
        logger.error(f"Failed to save query into MongoDB: {exc}")
        return ""

def list_queries(user_id: str, limit: int = 20) -> list[dict]:
    """Retrieves user's query and analysis history from MongoDB."""
    try:
        rows = database().queries.find({"user_id": ObjectId(user_id)}).sort("created_at", -1).limit(limit)
        return [serialize(row) for row in rows]
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error while listing queries."
        )

def save_attachment(user_id: str, filename: str, content_type: str, path: str, extracted_text: str = "") -> str:
    try:
        doc = {
            "user_id": ObjectId(user_id),
            "filename": filename,
            "content_type": content_type,
            "path": path,
            "extracted_text": extracted_text,
            "created_at": datetime.now(timezone.utc)
        }
        res = database().attachments.insert_one(doc)
        return str(res.inserted_id)
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error while saving attachment."
        )

def get_attachment(user_id: str, attachment_id: str) -> dict | None:
    try:
        return database().attachments.find_one({"_id": ObjectId(attachment_id), "user_id": ObjectId(user_id)})
    except Exception:
        return None
