from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router


PROJECT_ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="ChildGuard API", version="0.1.0", description="Local development API for the ChildGuard mock-analysis MVP.")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|.*\.app\.github\.dev|.*\.preview\.app\.github\.dev)",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/css", StaticFiles(directory=PROJECT_ROOT / "css"), name="css")
app.mount("/js", StaticFiles(directory=PROJECT_ROOT / "js"), name="js")


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "index.html")


app.include_router(router)
