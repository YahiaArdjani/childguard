from fastapi import APIRouter
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse, ModelInfoResponse
from app.services.analyzer import analyze_message

router = APIRouter()

MODEL_INFO = {
    "version": "childguard-nlp-1.0",
    "languages_supported": ["ar", "en"],
    "active_categories": ["Appearance", "Cussing", "Hatred", "Racial", "Sexual", "Violence", "NOT"],
    "architecture": "Arabic TF-IDF + One-vs-Rest Logistic Regression with calibrated thresholds; English deterministic keyword baseline",
}


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", model_loaded=True)


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    return ModelInfoResponse(**MODEL_INFO)

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a message with the persisted optimized NLP baseline."""
    return analyze_message(request.text)
