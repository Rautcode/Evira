"""Database initialization and management utilities."""

import os
import re
import logging
from typing import List
import pyodbc
from app.utils.db_connector import DBConnector

logger = logging.getLogger(__name__)

# Database name must be a safe identifier (used in a CREATE DATABASE statement,
# which cannot be parameterized).
_VALID_DB_NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]{0,127}$')


def ensure_database_exists():
    """Create the target database if it does not exist yet.

    The app connects directly to MSSQL_DATABASE, but on a fresh SQL Server that
    database won't exist. Connect to `master` first and create it so the app can
    bootstrap a brand-new server.
    """
    db_name = os.getenv("MSSQL_DATABASE", "scada_reports")
    if not _VALID_DB_NAME.match(db_name):
        raise ValueError(f"Unsafe MSSQL_DATABASE name: {db_name!r}")

    master = DBConnector(database="master")
    conn = master.get_connection()
    try:
        conn.autocommit = True  # CREATE DATABASE cannot run inside a transaction
        cursor = conn.cursor()
        cursor.execute(f"IF DB_ID('{db_name}') IS NULL CREATE DATABASE [{db_name}];")
        cursor.close()
        logger.info("Ensured database '%s' exists", db_name)
    finally:
        conn.close()


def initialize_database():
    """Initialize the database: ensure it exists, then apply Alembic migrations.

    Schema is now managed by versioned migrations (migrations/versions) instead
    of ad-hoc raw SQL execution, so it is deterministic and auditable (D42).
    """
    logging.info("Starting database initialization")

    # Bootstrap: make sure the target database exists before connecting to it.
    ensure_database_exists()

    from app.utils.migrations import run_migrations
    run_migrations()
    logging.info("Database initialization completed successfully")

def seed_test_data():
    """Seed the database with test data for development."""
    logging.info("Starting test data seeding")
    connector = DBConnector()
    
    try:
        conn = connector.get_connection()
        cursor = conn.cursor()
        
        # Check if activity logs already have data
        cursor.execute("SELECT COUNT(*) FROM activity_log")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO activity_log (event_type, description, severity, source)
                VALUES 
                ('report', 'Daily Production Report Generated', 'info', 'scheduler'),
                ('wincc', 'Connection restored', 'success', 'system'),
                ('user', 'New user account created', 'info', 'auth'),
                ('error', 'Database backup failed', 'error', 'backup');
            """)
        
        # Check if scheduled tasks already exist
        cursor.execute("SELECT COUNT(*) FROM scheduled_tasks")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO scheduled_tasks (name, task_type, schedule, status)
                VALUES 
                ('Daily Production Report', 'report', '0 6 * * *', 'active'),
                ('System Backup', 'backup', '0 0 * * 0', 'active'),
                ('Data Cleanup', 'maintenance', '0 2 * * *', 'active');
            """)

        # Check if Machines are already seeded
        cursor.execute("SELECT COUNT(*) FROM Machines")
        if cursor.fetchone()[0] == 0:
            logging.info("Seeding Machines data")
            cursor.execute("""
                INSERT INTO Machines (MachineID, MachineName, MachineType, Status, Location, Department)
                VALUES 
                ('M001', 'Extruder Alpha', 'Extrusion', 'active', 'Line 1, Hall A', 'Production'),
                ('M002', 'Molding Beta', 'Injection Molding', 'active', 'Line 2, Hall A', 'Production'),
                ('M003', 'Cooling Gamma', 'Chiller', 'active', 'Basement 1', 'Facilities'),
                ('M004', 'Packaging Delta', 'Packaging', 'active', 'Line 1, Hall B', 'Packaging'),
                ('M005', 'Mixer Epsilon', 'Blending', 'inactive', 'Line 3, Hall A', 'Production');
            """)

        # Seed reports history link
        cursor.execute("SELECT COUNT(*) FROM Reports")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO Reports (MachineID, ReportType)
                VALUES 
                ('M001', 'production_summary'),
                ('M001', 'downtime_analysis'),
                ('M002', 'production_summary');
            """)

        # Seed log telemetry data for machines (extending past few days)
        cursor.execute("SELECT COUNT(*) FROM logs")
        if cursor.fetchone()[0] == 0:
            logging.info("Seeding logs telemetry data")
            import random
            from datetime import datetime, timedelta
            
            shifts = ['Morning', 'Evening', 'Night']
            params = {
                'Extrusion': [('Temperature', 'C', 180, 220), ('Pressure', 'bar', 80, 120), ('Speed', 'RPM', 50, 75)],
                'Injection Molding': [('Clamping Force', 'kN', 500, 600), ('Cycle Time', 's', 15, 25)],
                'Chiller': [('Water Temp', 'C', 5, 12), ('Flow Rate', 'L/min', 100, 150)],
                'Packaging': [('Pack Count', 'pcs', 10, 30), ('Error Rate', '%', 0, 2)],
                'Blending': [('Mix Speed', 'RPM', 100, 200), ('Vessel Temp', 'C', 40, 60)]
            }
            
            log_entries = []
            now = datetime.now()
            machines_data = [
                ('M001', 'Extrusion'),
                ('M002', 'Injection Molding'),
                ('M003', 'Chiller'),
                ('M004', 'Packaging')
            ]
            
            for day in range(14):
                log_date = now - timedelta(days=day)
                for shift in shifts:
                    for m_id, m_type in machines_data:
                        for hour in range(3):
                            log_time = log_date.replace(hour=8 if shift == 'Morning' else (16 if shift == 'Evening' else 0)) + timedelta(hours=hour*2)
                            for param_name, unit, min_val, max_val in params[m_type]:
                                val = round(random.uniform(min_val, max_val), 2)
                                status = 'Normal'
                                if val > max_val * 0.95 or val < min_val * 1.05:
                                    status = 'Warning'
                                    
                                log_entries.append((m_id, shift, log_time, 'production_summary', param_name, val, unit, status))
                                log_entries.append((m_id, shift, log_time, 'downtime_analysis', param_name, val, unit, status))
                                log_entries.append((m_id, shift, log_time, 'quality_metrics', param_name, val, unit, status))

            # Insert in chunks of 100
            for i in range(0, len(log_entries), 100):
                chunk = log_entries[i:i+100]
                cursor.executemany("""
                    INSERT INTO logs (machine_id, shift, timestamp, report_type, parameter, value, unit, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, chunk)
            conn.commit()
            logging.info(f"Seeded {len(log_entries)} logs entries")
        
        conn.commit()
        logging.info("Test data seeded successfully")
        
    except Exception as e:
        logging.error(f"Error seeding test data: {e}")
        conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    try:
        initialize_database()
        seed_test_data()
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        exit(1)
