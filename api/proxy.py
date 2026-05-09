"""
Vercel Python Function — single-file proxy that re-applies the original
request path before delegating to the FastAPI app.

Vercel rewrites `/api/(.*) -> /api/proxy?_p=$1`, so this function receives
every API request with the captured suffix in `_p`. We restore `scope["path"]`
to `/api/<captured>`, then delegate to the FastAPI app whose routers are
mounted at both `/` and `/api/`.
"""

import os
import sys
from urllib.parse import parse_qs, urlencode

_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
_BACKEND_DIR = os.path.join(_REPO_ROOT, "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from app.main import app as _fastapi_app  # noqa: E402


async def app(scope, receive, send):
    if scope["type"] == "http":
        qs = scope.get("query_string", b"").decode("latin-1")
        params = parse_qs(qs, keep_blank_values=True)
        captured = params.pop("_p", [None])[0]
        if captured is not None:
            new_path = "/api/" + captured.lstrip("/")
            new_qs = urlencode(
                [(k, v) for k, vs in params.items() for v in vs], doseq=False
            )
            scope = dict(scope)
            scope["path"] = new_path
            scope["raw_path"] = new_path.encode()
            scope["query_string"] = new_qs.encode()
    await _fastapi_app(scope, receive, send)
