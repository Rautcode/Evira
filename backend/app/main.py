"""Main FastAPI application module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    dashboard, websocket, auth, charts, email, logger, report, scheduler, template, system_settings
)
from app.core.events import startup_event, shutdown_event
import logging

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register event handlers
app.add_event_handler("startup", lambda: startup_event(app))
app.add_event_handler("shutdown", lambda: shutdown_event(app))

# Register routers
app.include_router(dashboard.router)
app.include_router(websocket.router)
app.include_router(auth.router)
app.include_router(charts.router)
app.include_router(email.router)
app.include_router(logger.router)
app.include_router(report.router)
app.include_router(scheduler.router)
app.include_router(template.router)
app.include_router(system_settings.router)
