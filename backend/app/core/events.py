"""FastAPI application lifecycle events."""

import os
import logging

from fastapi import FastAPI
from app.services.wincc_service import wincc_monitor
from app.routers.scheduler import scheduler

logger = logging.getLogger(__name__)


async def startup_event(app: FastAPI):
    """Handle application startup."""
    try:
        from app.utils.db_init_new import initialize_database, seed_test_data
        from app.services.user_service import ensure_default_admin
        initialize_database()
        ensure_default_admin()
        # Demo/random seed data is opt-in only — never auto-populate a
        # production database with synthetic values (see DEFECTS D42).
        if os.getenv("SEED_DEMO_DATA", "0") == "1":
            seed_test_data()
            logger.info("Database initialized and demo data seeded on startup.")
        else:
            logger.info("Database schema initialized on startup (demo seed skipped).")
    except Exception as e:
        logger.error(f"Failed to auto-initialize database: {e}")

    # Start the scheduler here (single place) rather than at module import,
    # so it has a clean start/stop lifecycle tied to the app.
    if not scheduler.running:
        scheduler.start()
        logger.info("Background scheduler started.")

    await wincc_monitor.start()


async def shutdown_event(app: FastAPI):
    """Handle application shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped.")
    await wincc_monitor.stop()
