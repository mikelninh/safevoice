import os
import time
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=False)

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from app.routers import cases, analyze, reports, chain, upload, sla, partners, dashboard, auth, legal, policy


# ---------------------------------------------------------------------------
# CORS origins from environment (comma-separated)
# ---------------------------------------------------------------------------
_default_origins = "http://localhost:5173,http://localhost:8000"
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", _default_origins).split(",")
    if o.strip()
]


# ---------------------------------------------------------------------------
# Simple in-memory rate limiter (no external dependency needed at runtime)
# ---------------------------------------------------------------------------
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding-window rate limiter.

    Defaults: 60 requests per 60 seconds.
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        # Prune old entries
        self._hits[client_ip] = [
            t for t in self._hits[client_ip] if t > now - self.window
        ]
        if len(self._hits[client_ip]) >= self.max_requests:
            return Response("Rate limit exceeded", status_code=429)
        self._hits[client_ip].append(now)
        return await call_next(request)


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="SafeVoice API",
    description="Digital harassment documentation and reporting platform",
    version="0.1.0",
)

app.add_middleware(SecurityHeadersMiddleware)

if not os.environ.get("TESTING"):
    _rate_limit = int(os.environ.get("RATE_LIMIT_RPM", "120"))
    app.add_middleware(RateLimitMiddleware, max_requests=_rate_limit, window_seconds=60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers at both / and /api/ so frontend works in dev (proxy) and production (direct)
for r in [cases.router, analyze.router, reports.router, chain.router, upload.router,
          sla.router, partners.router, dashboard.router, auth.router, legal.router, policy.router]:
    app.include_router(r)
    app.include_router(r, prefix="/api")


# Initialize database on startup
from app.database import init_db, seed_categories_and_laws
init_db()
seed_categories_and_laws()


@app.get("/health")
def health():
    from app.services.classifier_llm import is_available as llm_ok
    from app.services.classifier_transformer import is_available as transformer_ok
    from app.database import SessionLocal, Category, Law
    db = SessionLocal()
    tier = "openai" if llm_ok() else ("transformer" if transformer_ok() else "regex")
    cats = db.query(Category).count()
    laws = db.query(Law).count()
    db.close()
    key = os.environ.get("OPENAI_API_KEY", "")
    key_info = f"{key[:5]}...{key[-4:]}" if len(key) > 10 else ("empty" if not key else "too_short")
    return {"status": "ok", "service": "SafeVoice API", "classifier_tier": tier, "db": {"categories": cats, "laws": laws}, "openai_key": key_info}


# ---------------------------------------------------------------------------
# Serve built frontend in production (static dir created by Docker build)
# ---------------------------------------------------------------------------
_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
