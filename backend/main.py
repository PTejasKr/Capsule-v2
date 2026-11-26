import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import init_db
from backend.services.brd_manager import BRDManager
from backend.routers import webhooks, api, profiles, auth

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("capsule.main")

_IS_PRODUCTION = os.environ.get("ENV", "production").lower() == "production"
_docs_url = None if _IS_PRODUCTION else "/docs"
_redoc_url = None if _IS_PRODUCTION else "/redoc"
_openapi_url = None if _IS_PRODUCTION else "/openapi.json"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Capsule API Service...")
    try:
        await init_db()
        brd_manager = BRDManager()
        await brd_manager.load_brd(profile_id=1)
    except Exception as e:
        logger.error(f"Startup initialization warning: {e}", exc_info=True)
    logger.info("Capsule API Service successfully started and ready to handle requests.")
    yield

app = FastAPI(
    title="Capsule — PR Analyzer API",
    description="Backend service for AI-powered PR analysis, workflow impact detection, and changelog generation.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request
from backend.middleware.rate_limiter import RateLimiterMiddleware

ALLOWED_ORIGINS = [
    "https://capsule-opal-nine.vercel.app",
    "chrome-extension://",  # Chrome extension origins are validated by API key
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Chrome extensions need wildcard; security is enforced by X-API-Key
    allow_credentials=False,      # Credentials=False with wildcard is safe and valid
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization", "x-hub-signature-256"],
)

# Enterprise Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimiterMiddleware, requests_per_minute=120)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "status": "error"}
    )

from backend.middleware.security import verify_github_signature
from fastapi import Depends

app.include_router(auth.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(webhooks.router)
app.include_router(api.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")

app.post("/api/webhook/github", status_code=200, dependencies=[Depends(verify_github_signature)])(webhooks.github_webhook)

from fastapi.responses import HTMLResponse, FileResponse

def find_static_file(*relative_segments):
    base_dirs = [
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    ]
    for b in base_dirs:
        candidate = os.path.join(b, *relative_segments)
        if os.path.exists(candidate):
            return candidate
    return None

@app.get("/admin", response_class=HTMLResponse)
def get_admin_page():
    options_html = find_static_file("extension", "options", "options.html")
    if options_html and os.path.exists(options_html):
        with open(options_html, "r", encoding="utf-8") as f:
            html = f.read()
            polyfill = """<link rel="manifest" href="/admin/manifest.webmanifest">
<meta name="theme-color" content="#d95f02">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Capsule">
<link rel="apple-touch-icon" href="/admin/icon128.png">
<script>
if (typeof chrome === "undefined" || !chrome.storage) {
  window.chrome = window.chrome || {};
  window.chrome.storage = {
    local: {
      get: (keys) => Promise.resolve((Array.isArray(keys) ? keys : [keys]).reduce((a, k) => { a[k] = localStorage.getItem(k) || ""; return a; }, {})),
      set: (obj) => { Object.entries(obj).forEach(([k, v]) => localStorage.setItem(k, v)); return Promise.resolve(); }
    }
  };
}
if (!window.chrome.identity) {
  window.chrome.identity = {
    getRedirectURL: () => window.location.origin + "/admin",
    launchWebAuthFlow: (details, callback) => {
      window.location.href = details.url;
    }
  };
}
if (!window.chrome.runtime) {
  window.chrome.runtime = { lastError: null };
}
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/admin/sw.js')
      .then(reg => console.log('Capsule PWA ServiceWorker registered:', reg.scope))
      .catch(err => console.log('Capsule PWA ServiceWorker registration error:', err));
  });
}
</script>"""
            html = html.replace('<head>', '<head>\n' + polyfill)
            html = html.replace('src="options.js"', 'src="/admin/options.js"')
            return HTMLResponse(content=html)
    return HTMLResponse("""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Capsule — System &amp; Resource Dashboard</title>
  <style>
    body{margin:0;font-family:Inter,Arial,sans-serif;background:#0d1117;color:#e6edf3;padding:32px}
    .wrap{max-width:860px;margin:0 auto}
    h1{font-size:20px;margin:0 0 6px}
    .sub{color:#8b949e;font-size:13px;margin-bottom:24px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:20px}
    .card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}
    .k{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.06em}
    .v{font-size:20px;font-weight:700;margin-top:6px}
    .ok{color:#3fb950}
    pre{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;font-size:12px;overflow:auto}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Capsule Telemetry &amp; Pipeline Admin</h1>
    <div class="sub">Minimal runtime resource monitor &amp; API health</div>
    <div class="grid">
      <div class="card"><div class="k">Service</div><div class="v ok" id="svc">Loading...</div></div>
      <div class="card"><div class="k">Database</div><div class="v" id="db">-</div></div>
      <div class="card"><div class="k">Memory RSS</div><div class="v" id="mem">-</div></div>
      <div class="card"><div class="k">Uptime</div><div class="v" id="up">-</div></div>
    </div>
    <pre id="raw">Fetching /api/resources...</pre>
  </div>
  <script>
    fetch('/api/resources').then(r=>r.json()).then(d=>{
      document.getElementById('svc').textContent=d.status.toUpperCase();
      document.getElementById('db').textContent=d.database;
      document.getElementById('mem').textContent=(d.memory_rss_mb!==null?d.memory_rss_mb+' MB':'N/A');
      document.getElementById('up').textContent=d.uptime_seconds+' s';
      document.getElementById('raw').textContent=JSON.stringify(d,null,2);
    }).catch(e=>{document.getElementById('raw').textContent=String(e);});
  </script>
</body>
</html>""")

import platform
import time as _time
_CAPSULE_START = _time.time()

def _capsule_rss_mb():
    try:
        with open("/proc/self/status", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return round(int(line.split()[1]) / 1024.0, 2)
    except OSError:
        pass
    return None

@app.get("/api/resources")
def get_resources():
    from backend.database import is_pg
    return {
        "status": "operational",
        "service": "capsule-api",
        "database": "postgresql" if is_pg() else "sqlite",
        "uptime_seconds": round(_time.time() - _CAPSULE_START, 2),
        "memory_rss_mb": _capsule_rss_mb(),
        "python_version": platform.python_version(),
        "vercel": bool(os.environ.get("VERCEL")),
        "rate_limit_rpm": 120,
    }

@app.get("/admin/options.js")
def get_admin_js():
    options_js = find_static_file("extension", "options", "options.js")
    if options_js and os.path.exists(options_js):
        return FileResponse(options_js, media_type="application/javascript")
    return HTMLResponse("// options.js not found", status_code=404)

@app.get("/admin/manifest.webmanifest")
def get_admin_manifest():
    manifest_path = find_static_file("extension", "options", "manifest.webmanifest")
    if manifest_path and os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="application/manifest+json")
    return JSONResponse({}, status_code=404)

@app.get("/admin/sw.js")
def get_admin_sw():
    sw_path = find_static_file("extension", "options", "sw.js")
    if sw_path and os.path.exists(sw_path):
        return FileResponse(sw_path, media_type="application/javascript")
    return HTMLResponse("// sw.js not found", status_code=404)

@app.get("/admin/icon128.png")
def get_admin_icon():
    icon_path = find_static_file("extension", "icons", "icon128.png")
    if icon_path and os.path.exists(icon_path):
        return FileResponse(icon_path, media_type="image/png")
    return HTMLResponse("Icon not found", status_code=404)

@app.get("/")
def read_root():
    return {
        "project": "Capsule",
        "status": "operational",
        "version": "1.0.0",
        "admin_dashboard": "/admin"
    }




