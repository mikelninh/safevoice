from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import cases, analyze, reports

app = FastAPI(
    title="SafeVoice API",
    description="Digital harassment documentation and reporting platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(analyze.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "SafeVoice API"}
