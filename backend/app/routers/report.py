from fastapi import APIRouter, HTTPException, status, UploadFile, File, Body, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os
import logging
import pandas as pd
from fpdf import FPDF
import uuid
import pyodbc
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.services.report_service import ReportService
from app.utils.db_connector import DBConnector
from app.utils.error_handler import handle_db_error
from app.utils.db import get_db_connection
from app.models.report_models import MachineListResponse, ReportGenerateResponse
from app.models.responses import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["report"], prefix="/report")

class ReportPayload(BaseModel):
    report_type: str  # 'pdf' or 'csv'
    data: list  # List of dicts (rows)
    file_name: str = None

class GenerateRequest(BaseModel):
    db_params: Optional[dict] = None
    date_range: dict
    machine_id: str
    shift: str
    report_type: str
    template_id: str
    output_type: str = 'pdf'
    with_chart: bool = False
    email_immediately: bool = False
    recipients: Optional[str] = None
    email_message: Optional[str] = None

class PreviewRequest(BaseModel):
    db_params: Optional[dict] = None
    date_range: dict
    machine_id: str
    shift: str
    report_type: str

@router.post("/generate")
def generate_report(data: GenerateRequest = Body(...)):
    service = ReportService(data.db_params)
    file_path = service.generate_report(
        date_range=data.date_range,
        machine_id=data.machine_id,
        shift=data.shift,
        report_type=data.report_type,
        template_id=data.template_id,
        output_type=data.output_type,
        with_chart=data.with_chart
    )
    
    # Save report generation history in database
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO report_history (report_type, template_id, parameters, status, file_path, created_by)
                VALUES (?, ?, ?, 'success', ?, 'System')
            """, (data.report_type, data.template_id, str(data.date_range), file_path))
            conn.commit()
            cursor.close()
    except Exception as e:
        logger.error(f"Failed to save report history to DB: {e}")

    # Email immediately if checked
    if data.email_immediately and data.recipients:
        try:
            from app.services.email_service import email_service
            recipients_list = [r.strip() for r in data.recipients.split(",") if r.strip()]
            for recipient in recipients_list:
                email_service.send_email(
                    subject=f"SCADA Report - {data.report_type.replace('_', ' ').capitalize()}",
                    body=data.email_message or "Please find the attached SCADA report.",
                    to_email=recipient,
                    attachment_path=file_path
                )
        except Exception as e:
            logger.error(f"Failed to send immediate report email: {e}")
        
    filename = os.path.basename(file_path)
    media_type = "application/pdf" if file_path.endswith(".pdf") else "text/csv"
    return FileResponse(file_path, filename=filename, media_type=media_type)

@router.post("/preview")
def preview_report_data(data: PreviewRequest = Body(...)):
    """Fetch logs to preview them in Step 3 of the report generator."""
    try:
        service = ReportService(data.db_params)
        logs = service.fetch_data(
            date_range=data.date_range,
            machine_id=data.machine_id,
            shift=data.shift,
            report_type=data.report_type
        )
        formatted_logs = []
        for i, log in enumerate(logs):
            formatted_logs.append({
                "id": str(log.get("id") or i + 1),
                "timestamp": log.get("timestamp").isoformat() if isinstance(log.get("timestamp"), datetime) else str(log.get("timestamp")),
                "machine": log.get("machine_id"),
                "parameter": log.get("parameter", "Unknown"),
                "value": log.get("value", 0),
                "unit": log.get("unit", ""),
                "included": True
            })
        return formatted_logs
    except Exception:
        logger.exception("Failed to preview report data")
        raise HTTPException(status_code=500, detail="Failed to preview report data")

@router.get("/list")
def list_reports():
    """Get list of previously generated reports from the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    id,
                    report_type,
                    template_id,
                    status,
                    created_at,
                    file_path,
                    created_by
                FROM report_history
                ORDER BY created_at DESC
            """
            cursor.execute(query)
            reports = []
            for row in cursor.fetchall():
                filename = os.path.basename(row.file_path) if row.file_path else f"report_{row.id}.pdf"
                reports.append({
                    "id": str(row.id),
                    "name": f"{row.report_type.replace('_', ' ').capitalize()} Report",
                    "title": f"{row.report_type.replace('_', ' ').capitalize()} ({row.template_id})",
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "status": row.status,
                    "filename": filename,
                    "created_by": row.created_by
                })
            cursor.close()
            return reports
    except Exception:
        logger.exception("Failed to fetch report history")
        raise HTTPException(status_code=500, detail="Failed to fetch report history")

@router.get("/download/{file_name}")
def download_report(file_name: str):
    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../reports'))
    file_path = os.path.join(reports_dir, file_name)
    # Security: Prevent path traversal attacks
    real_path = os.path.realpath(file_path)
    if not real_path.startswith(os.path.realpath(reports_dir)):
        raise HTTPException(status_code=403, detail="Access denied: invalid file path")
    if not os.path.exists(real_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(real_path, filename=os.path.basename(real_path))

def get_db():
    """Database dependency."""
    with get_db_connection() as conn:
        yield conn

@router.get("/machines", response_model=MachineListResponse)
@handle_db_error
async def get_machines(conn = Depends(get_db)):
    """Get list of available machines for reporting from the connected database."""
    try:
        cursor = conn.cursor()        # Query to get all machines from the database with detailed information
        query = """
            SELECT 
                m.MachineID as id,
                m.MachineName as name,
                m.MachineType as type,
                m.Status as status,
                m.LastActive as last_active,
                m.Location as location,
                m.Department as department,
                COUNT(r.ReportID) as total_reports
            FROM Machines m
            LEFT JOIN Reports r ON m.MachineID = r.MachineID
            WHERE m.IsActive = 1
            GROUP BY 
                m.MachineID, 
                m.MachineName, 
                m.MachineType, 
                m.Status, 
                m.LastActive,
                m.Location,
                m.Department
            ORDER BY m.MachineName
        """
        
        cursor.execute(query)
        machines = []
        for row in cursor.fetchall():
            machines.append({
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "status": row.status,
                "last_active": row.last_active.isoformat() if row.last_active else None,
                "location": row.location,
                "department": row.department,
                "total_reports": row.total_reports,
                "is_available": row.status.lower() == "active" if row.status else False
            })

        cursor.close()

        return MachineListResponse(
            message="Successfully retrieved machine list from database",
            data={"machines": machines}
        )
    except Exception:
        logger.exception("Failed to retrieve machine list")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve machine list"
        )

def get_machine_list():
    try:
        connector = DBConnector()
        conn = connector.get_connection()
        cursor = conn.cursor()
        # Adjust the table/column names as per your schema
        cursor.execute("SELECT DISTINCT machine_id FROM machines")
        machines = [row[0] for row in cursor.fetchall()]
        conn.close()
        return machines
    except Exception as e:
        # Log the error for debugging on the backend
        logger.error(f"Error fetching machine list: {e}")
        # Return an empty list in case of any error to prevent frontend TypeError
        return []

@router.get("/generate")
def generate_report_get():
    """Handle incorrect GET requests to generate endpoint"""
    raise HTTPException(
        status_code=405,
        detail="Method not allowed. Use POST to /report/generate with report configuration."
    )
