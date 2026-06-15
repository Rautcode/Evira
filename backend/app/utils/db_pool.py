"""Database connection pool and error handling."""

import logging
from contextlib import contextmanager
from typing import Any, Optional
import pyodbc
# Lazy load email_service to avoid circular import

logger = logging.getLogger(__name__)

class ConnectionPool:
    """Connection pool for database connections."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._pool = []
        self._active = 0

    def get_connection(self) -> Any:
        """Get a database connection from the pool."""
        # Reuse existing connection if available
        if self._pool:
            conn = self._pool.pop()
            # Test if connection is still alive
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return conn
            except Exception:
                logger.info("Discarding dead connection from pool")
                self._active -= 1
                try:
                    conn.close()
                except Exception:
                    pass
        
        if self._active >= self.max_connections:
            raise RuntimeError("Maximum database connections reached")
            
        try:
            from app.utils.db_connector import DBConnector
            connector = DBConnector()
            conn = connector.get_connection()
            self._active += 1
            return conn
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            self._send_alert("Database Connection Failed", str(e))
            raise

    def return_connection(self, conn: Any):
        """Return a connection to the pool."""
        if not conn:
            return
            
        try:
            # Check if connection is valid
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                is_valid = True
            except Exception:
                is_valid = False
                
            if is_valid and len(self._pool) < self.max_connections:
                self._pool.append(conn)
            else:
                self._active -= 1
                try:
                    conn.close()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Failed to return connection to pool: {e}")
            self._active -= 1

    def _send_alert(self, subject: str, message: str):
        """Send an alert email to admins."""
        try:
            from app.services.email_service import email_service
            admin_email = "admin@example.com"  # TODO: Get from config
            email_service.send_email(
                subject=subject,
                body=message,
                to_email=admin_email
            )
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")

# Global connection pool instance
pool = ConnectionPool()

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = pool.get_connection()
        yield conn
    except Exception as e:
        logger.error(f"Database error in connection context: {e}")
        raise
    finally:
        if conn:
            pool.return_connection(conn)
