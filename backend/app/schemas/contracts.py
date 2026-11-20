from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ReachPotential(BaseModel):
    score: int = Field(ge=0, le=100, description="Overall predicted reach potential score (0-100).")
    tier: Literal["Low", "Moderate", "High", "Viral Potential"] = Field(
        description="Reach potential tier based on score and platform distribution signals."
    )
    hook_strength: int = Field(ge=0, le=100, description="Stopping power of the opening lines (0-100).")
    algorithm_alignment: str = Field(
        description="How well the post aligns with the target platform's feed and discovery signals."
    )
    virality_drivers: list[str] = Field(
        default_factory=list,
        description="Specific elements that encourage shares, saves, or replies."
    )
    reach_limiters: list[str] = Field(
        default_factory=list,
        description="Factors that may suppress distribution or reduce retention."
    )


class ContentValue(BaseModel):
    score: int = Field(ge=0, le=100, description="Overall content value score (0-100).")
    clarity_score: int = Field(ge=0, le=100, description="Readability, pacing, and scannability (0-100).")
    originality_score: int = Field(ge=0, le=100, description="Freshness of insight vs. generic filler (0-100).")
    engagement_depth_score: int = Field(
        ge=0, le=100,
        description="Likelihood to spark thoughtful comments, saves, or bookmarks (0-100)."
    )
    value_proposition: str = Field(
        description="Core takeaway or utility the audience gains (educational, actionable, emotional, or authority-building)."
    )
    target_audience_fit: str = Field(
        description="Who this post resonates with most and why."
    )
    sentiment: str = Field(
        description="Primary emotional tone (e.g., Inspirational, Educational, Conversational, Authoritative, Urgent)."
    )


class ImprovementItem(BaseModel):
    priority: Literal["High", "Medium", "Low"]
    category: Literal[
        "Hook",
        "Structure",
        "Value & Depth",
        "Call to Action",
        "Formatting",
        "Hashtags & Discovery",
        "Visuals & Media",
    ]
    issue: str = Field(description="What is currently weak, unclear, or missing.")
    action: str = Field(description="Exact, concrete edit or addition to make.")
    expected_impact: str = Field(description="Why this change improves reach, retention, or conversion.")


class ActionableImprovements(BaseModel):
    suggested_hooks: list[str] = Field(
        min_length=1,
        description="2-3 stronger alternative opening hooks tailored to the platform."
    )
    improvements: list[ImprovementItem] = Field(
        min_length=1,
        description="Prioritized list of specific, actionable edits."
    )
    optimized_rewrite: str = Field(
        description="A ready-to-publish improved version of the post applying the top recommendations."
    )
    cta_suggestion: str = Field(
        description="A tailored call-to-action to drive comments, saves, or clicks."
    )
    hashtags: list[str] = Field(
        default_factory=list,
        description="3 to 6 targeted hashtags (each starting with '#') for discovery."
    )


class AnalysisCore(BaseModel):
    """Structured LLM output schema for social media content evaluation."""
    overall_score: int = Field(ge=0, le=100, description="Composite content effectiveness score (0-100).")
    executive_summary: str = Field(description="Concise 2-3 sentence overall assessment.")
    reach_potential: ReachPotential
    content_value: ContentValue
    actionable_improvements: ActionableImprovements


class AnalysisResponse(AnalysisCore):
    id: str | None = None
    platform: Literal["linkedin", "x", "instagram"]
    provider: Literal["gemini", "ollama"]
    model: str


class PostCreate(BaseModel):
    content: str = Field(min_length=3, max_length=5000)
    platform: Literal["linkedin", "x", "instagram"]
    impressions: int = Field(default=0, ge=0)
    engagement: int = Field(default=0, ge=0)
    analysis: AnalysisResponse | dict | None = None


class AnalyzeRequest(BaseModel):
    content: str = Field(min_length=3, max_length=5000)
    platform: Literal["linkedin", "x", "instagram"]
    attachment_id: str | None = None
    provider: Literal["gemini", "ollama"] | None = None
    model: str | None = None
    target_audience: str | None = Field(default=None, max_length=200)
    goal: Literal["reach", "engagement", "leads", "brand_awareness"] | None = None
