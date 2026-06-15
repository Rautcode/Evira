from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

from app.routers.auth import router as auth_router
from app.routers.report import router as report_router
from app.routers.template import router as template_router
from app.routers.email import router as email_router
from app.routers.logger import router as logger_router
from app.routers.scheduler import router as scheduler_router
from app.routers.charts import router as charts_router
from app.routers.dashboard import router as dashboard_router
from app.routers.websocket import router as websocket_router

app = FastAPI()

# Configure CORS and other middleware
origins = [
    "http://localhost:3000",
    "http://localhost:9002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:9002"
]

# Add all middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    return response

# Security headers middleware — injected on every response
# Satisfies OWASP baseline: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP, Permissions-Policy
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # CSP: allow 'unsafe-inline' for script-src so Swagger UI (/docs) renders correctly
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

# Register all routers with proper prefixes and tags
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(report_router, prefix="/report", tags=["reports"])
app.include_router(template_router, prefix="/template", tags=["templates"])
app.include_router(email_router, prefix="/email", tags=["email"])
app.include_router(logger_router, prefix="/logger", tags=["logging"])
app.include_router(scheduler_router, prefix="/scheduler", tags=["scheduling"])
app.include_router(charts_router, prefix="/charts", tags=["charts"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])

# Serve static files for reports (PDF/CSV downloads)
app.mount("/static/reports", StaticFiles(directory="reports"), name="reports")

# Add root help endpoint
@app.get("/")
@app.get("")  # Handle empty path
async def root():
    """API help and documentation"""
    return {
        "app": "SCADA Report Automation Tool API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": {
                "login": {"method": "POST", "path": "/auth/login", "description": "Login with SQL Server or Windows credentials"}
            },
            "dashboard": {
                "overview": {"method": "GET", "path": "/dashboard", "description": "Get dashboard overview"},
                "stats": {"method": "GET", "path": "/dashboard/stats", "description": "Get detailed dashboard statistics"},
                "websocket": {"protocol": "WS", "path": "/ws/dashboard", "description": "WebSocket for real-time updates"}
            },
            "report": {
                "generate": {"method": "POST", "path": "/report/generate", "description": "Generate a new report"},
                "download": {"method": "GET", "path": "/report/{report_id}", "description": "Download a generated report"}
            },
            "docs": {
                "swagger": {"method": "GET", "path": "/docs", "description": "OpenAPI documentation"},
                "redoc": {"method": "GET", "path": "/redoc", "description": "ReDoc documentation"}
            }
        }
    }

@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc: HTTPException):
    path = request.url.path
    method = request.method
    allowed_methods = {
        "/auth/login": ["POST"],
        "/report/generate": ["POST"],
        "/dashboard": ["GET"],
        "/dashboard/stats": ["GET"],
    }
    suggested_method = allowed_methods.get(path, ["unknown"])[0]
    
    return JSONResponse(
        status_code=405,
        content={
            "error": "Method Not Allowed",
            "detail": f"Method {method} not allowed for {path}. Use {suggested_method} instead.",
            "docs_url": f"{request.base_url}docs#/{path.split('/')[1]}"
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    path = request.url.path
    suggestions = {
        "/dashboard": "/dashboard",
        "/stats": "/dashboard/stats",
        "/login": "/auth/login",
        "/generate": "/report/generate"
    }
    suggested_path = suggestions.get(path, None)
    
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": f"Path {path} not found.",
            "suggestion": f"Did you mean {suggested_path}?" if suggested_path else "Check the API documentation for available endpoints.",
            "docs_url": f"{request.base_url}docs"
        }
    )
