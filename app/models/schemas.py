from typing import Literal
from pydantic import BaseModel, Field, field_validator

MAX_TEXT_LENGTH = 1000
Category = Literal["safe", "Appearance", "Cussing", "Hatred", "Racial", "Sexual", "Violence", "NOT"]
Severity = Literal["safe", "low", "medium", "high"]
Language = Literal["ar", "en"]

class AnalyzeRequest(BaseModel):
    text: str = Field(..., max_length=MAX_TEXT_LENGTH, description="Message to analyze")

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text must not be empty or whitespace only.")
        return value

class AnalyzeResponse(BaseModel):
    is_harmful: bool
    category: Category
    categories: list[Category]
    severity: Severity
    confidence: float = Field(..., ge=0, le=1)
    explanation: str
    language: Language


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model_loaded: bool


class ModelInfoResponse(BaseModel):
    version: str
    languages_supported: list[Language]
    active_categories: list[Category]
    architecture: str
