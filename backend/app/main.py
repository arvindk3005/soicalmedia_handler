from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .core.config import get_settings
from .db.mongodb import init_mongodb

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure upload directory exists
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    # Initialize MongoDB connection and indexes
    init_mongodb()
    yield

app = FastAPI(
    title=settings.app_name,
    description="Social media content intelligence API powered by FastAPI, MongoDB, Gemini & Ollama.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend access
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
