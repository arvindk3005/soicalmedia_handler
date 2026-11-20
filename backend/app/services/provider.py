import base64
import json
import logging
import re
from pathlib import Path
from fastapi import HTTPException, status
import httpx
from pydantic import ValidationError
from ..core.config import get_settings
from ..schemas.contracts import AnalysisCore

logger = logging.getLogger("pulsepilot.ai")

PROMPT_TEMPLATE = """You are a senior social media strategist, algorithm analyst, and copywriting optimization expert.
Evaluate the following draft post for {platform} across three core pillars:
1. Post Reach Potential (algorithmic alignment, scroll-stopping hook strength, virality drivers, and reach limiters).
2. Content Value (clarity/scannability, originality, engagement depth, value proposition, audience fit, and sentiment).
3. Actionable Improvements (alternative hooks, prioritized concrete edits, a ready-to-publish optimized rewrite, a tailored CTA, and discovery hashtags).

Draft Post:
\"\"\"{content}\"\"\"
{audience_section}{goal_section}{context_section}

Return ONLY a single valid JSON object matching this exact schema (no markdown, no extra text):
{{
  "overall_score": <integer 0-100>,
  "executive_summary": "<2-3 sentence overall assessment>",
  "reach_potential": {{
    "score": <integer 0-100>,
    "tier": "<one of: Low | Moderate | High | Viral Potential>",
    "hook_strength": <integer 0-100>,
    "algorithm_alignment": "<how well this fits {platform} feed & discovery signals>",
    "virality_drivers": ["<specific driver 1>", "<specific driver 2>"],
    "reach_limiters": ["<specific limiter 1>", "<specific limiter 2>"]
  }},
  "content_value": {{
    "score": <integer 0-100>,
    "clarity_score": <integer 0-100>,
    "originality_score": <integer 0-100>,
    "engagement_depth_score": <integer 0-100>,
    "value_proposition": "<what the reader gains from this post>",
    "target_audience_fit": "<who this resonates with most and why>",
    "sentiment": "<primary emotional tone, e.g. Educational, Inspirational, Authoritative, Conversational>"
  }},
  "actionable_improvements": {{
    "suggested_hooks": ["<alternative hook 1>", "<alternative hook 2>"],
    "improvements": [
      {{
        "priority": "<one of: High | Medium | Low>",
        "category": "<one of: Hook | Structure | Value & Depth | Call to Action | Formatting | Hashtags & Discovery | Visuals & Media>",
        "issue": "<what is currently weak or missing>",
        "action": "<exact concrete change to make>",
        "expected_impact": "<why this change improves reach or engagement>"
      }}
    ],
    "optimized_rewrite": "<complete, ready-to-publish improved version of the post for {platform}>",
    "cta_suggestion": "<specific call-to-action to drive comments, saves, or clicks>",
    "hashtags": ["#Tag1", "#Tag2", "#Tag3"]
  }}
}}"""

GEMINI_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "overall_score": {"type": "INTEGER"},
        "executive_summary": {"type": "STRING"},
        "reach_potential": {
            "type": "OBJECT",
            "properties": {
                "score": {"type": "INTEGER"},
                "tier": {
                    "type": "STRING",
                    "enum": ["Low", "Moderate", "High", "Viral Potential"],
                },
                "hook_strength": {"type": "INTEGER"},
                "algorithm_alignment": {"type": "STRING"},
                "virality_drivers": {"type": "ARRAY", "items": {"type": "STRING"}},
                "reach_limiters": {"type": "ARRAY", "items": {"type": "STRING"}},
            },
            "required": [
                "score",
                "tier",
                "hook_strength",
                "algorithm_alignment",
                "virality_drivers",
                "reach_limiters",
            ],
        },
        "content_value": {
            "type": "OBJECT",
            "properties": {
                "score": {"type": "INTEGER"},
                "clarity_score": {"type": "INTEGER"},
                "originality_score": {"type": "INTEGER"},
                "engagement_depth_score": {"type": "INTEGER"},
                "value_proposition": {"type": "STRING"},
                "target_audience_fit": {"type": "STRING"},
                "sentiment": {"type": "STRING"},
            },
            "required": [
                "score",
                "clarity_score",
                "originality_score",
                "engagement_depth_score",
                "value_proposition",
                "target_audience_fit",
                "sentiment",
            ],
        },
        "actionable_improvements": {
            "type": "OBJECT",
            "properties": {
                "suggested_hooks": {"type": "ARRAY", "items": {"type": "STRING"}},
                "improvements": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "priority": {
                                "type": "STRING",
                                "enum": ["High", "Medium", "Low"],
                            },
                            "category": {
                                "type": "STRING",
                                "enum": [
                                    "Hook",
                                    "Structure",
                                    "Value & Depth",
                                    "Call to Action",
                                    "Formatting",
                                    "Hashtags & Discovery",
                                    "Visuals & Media",
                                ],
                            },
                            "issue": {"type": "STRING"},
                            "action": {"type": "STRING"},
                            "expected_impact": {"type": "STRING"},
                        },
                        "required": [
                            "priority",
                            "category",
                            "issue",
                            "action",
                            "expected_impact",
                        ],
                    },
                },
                "optimized_rewrite": {"type": "STRING"},
                "cta_suggestion": {"type": "STRING"},
                "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
            },
            "required": [
                "suggested_hooks",
                "improvements",
                "optimized_rewrite",
                "cta_suggestion",
                "hashtags",
            ],
        },
    },
    "required": [
        "overall_score",
        "executive_summary",
        "reach_potential",
        "content_value",
        "actionable_improvements",
    ],
}

TIER_MAP = {
    "low": "Low",
    "moderate": "Moderate",
    "medium": "Moderate",
    "high": "High",
    "viral": "Viral Potential",
    "viral potential": "Viral Potential",
}

PRIORITY_MAP = {
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}

CATEGORY_MAP = {
    "hook": "Hook",
    "structure": "Structure",
    "value & depth": "Value & Depth",
    "value and depth": "Value & Depth",
    "value": "Value & Depth",
    "call to action": "Call to Action",
    "cta": "Call to Action",
    "formatting": "Formatting",
    "hashtags & discovery": "Hashtags & Discovery",
    "hashtags": "Hashtags & Discovery",
    "visuals & media": "Visuals & Media",
    "visuals": "Visuals & Media",
}


def _clamp_score(value: object, default: int = 50) -> int:
    try:
        num = int(round(float(value)))  # type: ignore[arg-type]
        return max(0, min(100, num))
    except (TypeError, ValueError):
        return default


def _normalize_analysis(data: dict) -> dict:
    """Normalizes LLM output before strict Pydantic validation."""
    reach = data.get("reach_potential") or {}
    reach_score = _clamp_score(reach.get("score"))
    raw_tier = str(reach.get("tier", "")).strip().lower()
    if raw_tier in TIER_MAP:
        reach["tier"] = TIER_MAP[raw_tier]
    else:
        reach["tier"] = (
            "Viral Potential" if reach_score >= 85
            else "High" if reach_score >= 65
            else "Moderate" if reach_score >= 40
            else "Low"
        )
    reach["score"] = reach_score
    reach["hook_strength"] = _clamp_score(reach.get("hook_strength"), reach_score)
    if not isinstance(reach.get("virality_drivers"), list):
        reach["virality_drivers"] = []
    if not isinstance(reach.get("reach_limiters"), list):
        reach["reach_limiters"] = []
    data["reach_potential"] = reach

    val = data.get("content_value") or {}
    val_score = _clamp_score(val.get("score"))
    val["score"] = val_score
    val["clarity_score"] = _clamp_score(val.get("clarity_score"), val_score)
    val["originality_score"] = _clamp_score(val.get("originality_score"), val_score)
    val["engagement_depth_score"] = _clamp_score(val.get("engagement_depth_score"), val_score)
    data["content_value"] = val

    if "overall_score" not in data or data["overall_score"] is None:
        data["overall_score"] = round((reach_score + val_score) / 2)
    else:
        data["overall_score"] = _clamp_score(data["overall_score"])

    imp_block = data.get("actionable_improvements") or {}
    if not isinstance(imp_block.get("suggested_hooks"), list) or not imp_block["suggested_hooks"]:
        imp_block["suggested_hooks"] = ["Lead with a concrete outcome or provocative question."]

    raw_items = imp_block.get("improvements")
    normalized_items = []
    if isinstance(raw_items, list):
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            prio = PRIORITY_MAP.get(str(item.get("priority", "medium")).strip().lower(), "Medium")
            cat = CATEGORY_MAP.get(str(item.get("category", "structure")).strip().lower(), "Structure")
            normalized_items.append({
                "priority": prio,
                "category": cat,
                "issue": str(item.get("issue") or "Needs refinement."),
                "action": str(item.get("action") or "Tighten phrasing and add concrete detail."),
                "expected_impact": str(item.get("expected_impact") or "Improves reader retention and engagement."),
            })
    if not normalized_items:
        normalized_items.append({
            "priority": "High",
            "category": "Hook",
            "issue": "Opening line could be more specific.",
            "action": "Lead with a clear outcome, tension, or contrarian insight.",
            "expected_impact": "Increases scroll-stop rate and dwell time.",
        })
    imp_block["improvements"] = normalized_items

    raw_tags = imp_block.get("hashtags")
    if isinstance(raw_tags, list):
        imp_block["hashtags"] = [
            tag if str(tag).startswith("#") else f"#{str(tag).lstrip('#')}"
            for tag in raw_tags
            if str(tag).strip()
        ]
    else:
        imp_block["hashtags"] = []

    data["actionable_improvements"] = imp_block
    return data


def extract_and_parse_json(raw_text: str) -> dict:
    """Safely extracts, parses, and validates LLM JSON output against AnalysisCore."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        raw_data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse LLM JSON output: {raw_text}")
        raise ValueError(f"Model returned invalid JSON format: {exc}")

    if not isinstance(raw_data, dict):
        raise ValueError("Model output must be a JSON object.")

    normalized = _normalize_analysis(raw_data)
    try:
        validated = AnalysisCore.model_validate(normalized)
    except ValidationError as exc:
        logger.error(f"LLM output failed schema validation: {exc}")
        raise ValueError(f"Model output did not match required analysis schema: {exc}")

    return validated.model_dump()


def _build_prompt(
    content: str,
    platform: str,
    attachment: dict | None = None,
    target_audience: str | None = None,
    goal: str | None = None,
) -> str:
    audience_section = f"\nTarget Audience: {target_audience}" if target_audience else ""
    goal_section = f"\nPrimary Campaign Goal: {goal}" if goal else ""
    context_section = ""
    if attachment and attachment.get("extracted_text"):
        context_section = f"\nAttached Document Content:\n{attachment['extracted_text'][:8000]}"

    return PROMPT_TEMPLATE.format(
        platform=platform.capitalize(),
        content=content,
        audience_section=audience_section,
        goal_section=goal_section,
        context_section=context_section,
    )


def analyze_with_gemini(
    content: str,
    platform: str,
    attachment: dict | None = None,
    model: str | None = None,
    target_audience: str | None = None,
    goal: str | None = None,
) -> dict:
    settings = get_settings()
    api_key = settings.gemini_api_key.strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gemini API key is not configured. Please add GEMINI_API_KEY to backend/.env (get a free key at https://aistudio.google.com) or select Ollama."
        )

    model_name = model or settings.gemini_model or "gemini-1.5-flash"
    prompt = _build_prompt(content, platform, attachment, target_audience, goal)
    parts: list[dict] = [{"text": prompt}]

    # Multimodal image attachment
    if attachment and attachment.get("content_type", "").startswith("image/"):
        file_path = Path(attachment["path"])
        if file_path.exists():
            img_bytes = file_path.read_bytes()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": attachment["content_type"],
                    "data": img_b64
                }
            })

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": GEMINI_RESPONSE_SCHEMA,
            "temperature": 0.35,
        }
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            response = client.post(url, json=payload)
            if response.status_code != 200:
                err_data = response.json().get("error", {})
                err_msg = err_data.get("message", response.text)
                logger.error(f"Gemini API returned error {response.status_code}: {err_msg}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Google Gemini API error ({response.status_code}): {err_msg}"
                )

            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if not candidates or "content" not in candidates[0]:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Google Gemini returned an empty response."
                )

            part_text = candidates[0]["content"]["parts"][0].get("text", "")
            result = extract_and_parse_json(part_text)
            result["platform"] = platform
            result["provider"] = "gemini"
            result["model"] = model_name
            return result

    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Google Gemini API. Please check your internet connection."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Google Gemini API request timed out after 45 seconds."
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during Gemini analysis")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini analysis failed: {exc}"
        )


def analyze_with_ollama(
    content: str,
    platform: str,
    attachment: dict | None = None,
    model: str | None = None,
    target_audience: str | None = None,
    goal: str | None = None,
) -> dict:
    settings = get_settings()
    base_url = settings.ollama_base_url.rstrip("/")
    model_name = model or settings.ollama_model or "llama3.2"

    prompt = _build_prompt(content, platform, attachment, target_audience, goal)
    data: dict = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    # Vision support if an image is attached
    if attachment and attachment.get("content_type", "").startswith("image/"):
        file_path = Path(attachment["path"])
        if file_path.exists():
            data["images"] = [base64.b64encode(file_path.read_bytes()).decode("utf-8")]

    endpoint = f"{base_url}/api/generate"

    try:
        with httpx.Client(timeout=90.0) as client:
            response = client.post(endpoint, json=data)

            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=(
                        f"Ollama model '{model_name}' was not found. "
                        f"Run 'ollama pull {model_name}' in your terminal, or switch to Gemini in the provider dropdown."
                    )
                )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Ollama server returned error status {response.status_code}: {response.text}"
                )

            resp_payload = response.json()
            raw_output = resp_payload.get("response", "")
            result = extract_and_parse_json(raw_output)
            result["platform"] = platform
            result["provider"] = "ollama"
            result["model"] = model_name
            return result

    except (httpx.ConnectError, ConnectionRefusedError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Could not connect to Ollama at {base_url}. "
                "Ensure Ollama is running (`ollama serve`) on your computer, or switch to Google Gemini."
            )
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Ollama request timed out after 90 seconds for model '{model_name}'. Local LLMs on CPU may need more time."
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during Ollama analysis")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama analysis failed: {exc}"
        )


def analyze_content(
    content: str,
    platform: str,
    attachment: dict | None = None,
    provider: str | None = None,
    model: str | None = None,
    target_audience: str | None = None,
    goal: str | None = None,
) -> dict:
    settings = get_settings()
    active_provider = (provider or settings.ai_provider or "gemini").lower().strip()

    if active_provider == "gemini":
        return analyze_with_gemini(content, platform, attachment, model, target_audience, goal)
    elif active_provider == "ollama":
        return analyze_with_ollama(content, platform, attachment, model, target_audience, goal)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported AI provider '{active_provider}'. Supported providers are: 'gemini', 'ollama'."
        )
