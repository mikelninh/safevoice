import os
import time
from collections import defaultdict

try:
    from dotenv import load_dotenv

    _env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path, override=False)
except ImportError:
    pass

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from app.routers import (
    cases,
    analyze,
    reports,
    chain,
    upload,
    sla,
    partners,
    dashboard,
    auth,
    legal,
    policy,
    orgs,
    bulk_import,
    agent,
)


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
for r in [
    cases.router,
    analyze.router,
    reports.router,
    chain.router,
    upload.router,
    sla.router,
    partners.router,
    dashboard.router,
    auth.router,
    legal.router,
    policy.router,
    orgs.router,
    bulk_import.router,
    agent.router,
]:
    app.include_router(r)
    app.include_router(r, prefix="/api")


# Initialize database on startup. Wrapped in try/except so a slow or briefly
# unreachable database during a serverless cold start does NOT crash the
# whole function — endpoints can still surface a 503 with a clear error.
from app.database import init_db, seed_categories_and_laws

try:
    init_db()
    seed_categories_and_laws()
except Exception as _db_err:  # pragma: no cover
    import logging

    logging.getLogger(__name__).error("Startup DB init failed: %s", _db_err)


@app.get("/health")
@app.get("/api/health")
def health():
    from app.services.classifier import is_configured as classifier_configured
    from app.database import SessionLocal, Category, Law

    db = SessionLocal()
    cats = db.query(Category).count()
    laws = db.query(Law).count()
    db.close()
    return {
        "status": "ok" if classifier_configured() else "degraded",
        "service": "SafeVoice API",
        "classifier": "llm" if classifier_configured() else "unavailable",
        "db": {"categories": cats, "laws": laws},
    }


# ---------------------------------------------------------------------------
# Serve built frontend in production (static dir created by Docker build)
# ---------------------------------------------------------------------------
_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
