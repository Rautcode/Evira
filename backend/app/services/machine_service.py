"""Service for handling machine-related operations."""

import logging
from typing import List, Dict, Any
from app.utils.db import get_db_connection
from app.utils.error_handler import handle_db_error

logger = logging.getLogger(__name__)

class MachineService:
    @staticmethod
    @handle_db_error
    def get_all_machines() -> List[Dict[str, Any]]:
        """Get list of all active machines from the database."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                query = """
                    SELECT 
                        MachineID as id,
                        MachineName as name,
                        MachineType as type,
                        Status as status,
                        LastActive as last_active
                    FROM Machines 
                    WHERE IsActive = 1
                    ORDER BY MachineName
                """
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                machines = []
                for row in cursor.fetchall():
                    machine = dict(zip(columns, row))
                    if machine.get('last_active'):
                        machine['last_active'] = machine['last_active'].isoformat()
                    machines.append(machine)
                return machines
            finally:
                cursor.close()

    @staticmethod
    @handle_db_error
    def get_machine_details(machine_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific machine."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                query = """
                    SELECT 
                        m.MachineID as id,
                        m.MachineName as name,
                        m.MachineType as type,
                        m.Status as status,
                        m.LastActive as last_active,
                        m.Description as description,
                        m.Location as location,
                        m.Department as department
                    FROM Machines m
                    WHERE m.MachineID = ? AND m.IsActive = 1
                """
                cursor.execute(query, (machine_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                columns = [column[0] for column in cursor.description]
                machine = dict(zip(columns, row))
                if machine.get('last_active'):
                    machine['last_active'] = machine['last_active'].isoformat()
                return machine
            finally:
                cursor.close()
