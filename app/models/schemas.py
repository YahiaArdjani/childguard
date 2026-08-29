from typing import Literal
from pydantic import BaseModel, Field, field_validator

MAX_TEXT_LENGTH = 1000
Category = Literal["safe", "insult", "bullying", "threat", "harassment", "other_harmful"]
Severity = Literal["low", "medium", "high"]

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
    severity: Severity
    confidence: float = Field(..., ge=0, le=1)
    explanation: str
