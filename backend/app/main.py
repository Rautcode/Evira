"""Main FastAPI application module."""

import os
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    dashboard, websocket, auth, charts, email, logger, report, scheduler, template, system_settings, tag_mapping
)
from app.core.events import startup_event, shutdown_event
from app.core.security import get_current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

app = FastAPI(
    title="SCADA Assistant API",
    description="API for SCADA Assistant application",
    version="1.0.0"
)

# CORS: restrict to configured origins. Set CORS_ALLOW_ORIGINS as a
# comma-separated list (e.g. "http://localhost:3000,https://scada.example.com").
_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000")
allowed_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers that require a valid Bearer token. Auth (login/logout) stays public,
# and websocket routes handle their own auth at connect time.
_protected = [Depends(get_current_user)]

# Register event handlers. These must be coroutine functions so Starlette
# awaits them — a sync lambda returning a coroutine is never awaited.
@app.on_event("startup")
async def _on_startup():
    await startup_event(app)

@app.on_event("shutdown")
async def _on_shutdown():
    await shutdown_event(app)

# Register routers. Public: auth, websocket. All others require auth.
app.include_router(auth.router)
app.include_router(websocket.router)
app.include_router(dashboard.router, dependencies=_protected)
app.include_router(charts.router, dependencies=_protected)
app.include_router(email.router, dependencies=_protected)
app.include_router(logger.router, dependencies=_protected)
app.include_router(report.router, dependencies=_protected)
app.include_router(scheduler.router, dependencies=_protected)
app.include_router(template.router, dependencies=_protected)
app.include_router(system_settings.router, dependencies=_protected)
app.include_router(tag_mapping.router, dependencies=_protected)
