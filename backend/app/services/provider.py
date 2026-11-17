import json, urllib.request
from fastapi import HTTPException
from ..core.config import get_settings
from .analytics import analyze_demo

def analyze_content(content: str, platform: str) -> dict:
    settings = get_settings()
    if settings.ai_provider.lower() == "demo": return analyze_demo(content, platform)
    if settings.ai_provider.lower() != "ollama": raise HTTPException(500, "AI_PROVIDER must be demo or ollama")
    prompt = f"Return JSON with sentiment, summary, hashtags, recommendation, suggested_hook. Analyze this {platform} post: {content}"
    request = urllib.request.Request(f"{settings.ollama_base_url.rstrip('/')}/api/generate", data=json.dumps({"model": settings.ollama_model, "prompt": prompt, "stream": False, "format": "json"}).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(json.loads(response.read())["response"])
        result["provider"] = "ollama"; return result
    except Exception as exc:
        raise HTTPException(502, f"Ollama analysis failed: {exc}")
