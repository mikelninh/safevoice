from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import cases, analyze, reports, chain, upload, sla, partners, dashboard, auth, legal, policy

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
app.include_router(chain.router)
app.include_router(upload.router)
app.include_router(sla.router)
app.include_router(partners.router)
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(legal.router)
app.include_router(policy.router)


@app.get("/health")
def health():
    from app.services.classifier_llm import is_available as llm_ok
    from app.services.classifier_transformer import is_available as transformer_ok
    tier = "claude_api" if llm_ok() else ("transformer" if transformer_ok() else "regex")
    return {"status": "ok", "service": "SafeVoice API", "classifier_tier": tier}
