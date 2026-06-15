"""FastAPI application lifecycle events."""

from fastapi import FastAPI
from app.services.wincc_service import wincc_monitor

async def startup_event(app: FastAPI):
    """Handle application startup."""
    import logging
    try:
        from app.utils.db_init_new import initialize_database, seed_test_data
        initialize_database()
        seed_test_data()
        logging.info("Database initialized and seeded successfully on startup.")
    except Exception as e:
        logging.error(f"Failed to auto-initialize database: {e}")
        
    await wincc_monitor.start()

async def shutdown_event(app: FastAPI):
    """Handle application shutdown."""
    await wincc_monitor.stop()
