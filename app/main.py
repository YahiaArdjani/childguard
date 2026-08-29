from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(title="ChildGuard API", version="0.1.0", description="Local development API for the ChildGuard mock-analysis MVP.")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"], allow_credentials=False, allow_methods=["POST"], allow_headers=["Content-Type"])
app.include_router(router)
