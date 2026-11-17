from pydantic import BaseModel, EmailStr, Field
from typing import Literal

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
class TokenResponse(BaseModel): access_token: str; token_type: str = "bearer"
class PostCreate(BaseModel):
    content: str = Field(min_length=3, max_length=3000)
    platform: Literal["linkedin", "x", "instagram"]
    impressions: int = Field(default=0, ge=0)
    engagement: int = Field(default=0, ge=0)
class AnalyzeRequest(BaseModel):
    content: str = Field(min_length=3, max_length=3000)
    platform: Literal["linkedin", "x", "instagram"]
