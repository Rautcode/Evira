"""Test server for verifying backend functionality."""
try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
    import logging
    import asyncio
    from typing import Dict, List
    from datetime import datetime
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please run: pip install fastapi pydantic uvicorn python-multipart websockets")
    exit(1)
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Test Server")

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:9002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:9002"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    return response

# Test REST endpoints
@app.get("/")
async def root():
    """Root endpoint to verify server is running."""
    return {
        "status": "ok",
        "message": "Test server is running",
        "available_endpoints": {
            "dashboard": "/dashboard",
            "stats": "/dashboard/stats",
            "auth": "/auth/login",
            "report": "/report/generate"
        }
    }

@app.get("/dashboard")
@app.get("/dashboard/")
async def get_dashboard():
    """Dashboard overview endpoint."""
    return {
        "status": "ok",
        "timestamp": str(datetime.now()),
        "message": "Welcome to the Test Dashboard"
    }

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Test endpoint for dashboard statistics."""
    return {
        "connection_status": True,
        "recent_events": [
            {"id": 1, "timestamp": str(datetime.now()), "type": "TEST_EVENT", "description": "Test event 1"},
            {"id": 2, "timestamp": str(datetime.now()), "type": "TEST_EVENT", "description": "Test event 2"}
        ],
        "scheduled_tasks": [
            {"id": 1, "name": "Test Task 1", "next_run": str(datetime.now())},
            {"id": 2, "name": "Test Task 2", "next_run": str(datetime.now())}
        ],
        "recent_reports": [
            {"id": 1, "name": "Test Report 1", "generated": str(datetime.now())},
            {"id": 2, "name": "Test Report 2", "generated": str(datetime.now())}
        ]
    }

# Test auth endpoints
class LoginPayload(BaseModel):
    server: str
    database: str
    auth_mode: str
    username: str = None
    password: str = None

@app.post("/auth/login")
async def login(data: LoginPayload):
    """Test endpoint for SQL Server authentication."""
    try:
        # Simulate authentication check
        if data.auth_mode == "windows":
            # Simulate Windows authentication
            if data.server and data.database:
                return {"message": "Windows authentication successful"}
            raise HTTPException(status_code=401, detail="Invalid server or database")
        else:
            # Simulate SQL authentication
            if data.username and data.password:
                return {"message": "SQL authentication successful"}
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

class ReportPayload(BaseModel):
    report_type: str  # 'pdf' or 'csv'
    template_id: str
    parameters: Dict

@app.post("/report/generate")
async def generate_report(data: ReportPayload):
    """Test endpoint for report generation."""
    try:
        # Simulate report generation
        return {
            "message": f"{data.report_type.upper()} report generation triggered",
            "status": "success",
            "template_id": data.template_id,
            "download_url": f"/reports/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{data.report_type}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/template/save")
async def save_template(template_data: Dict):
    """Test endpoint for saving report templates."""
    try:
        return {
            "message": "Template saved successfully",
            "template_id": f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/email/send")
async def send_email(email_data: Dict):
    """Test endpoint for sending emails."""
    try:
        return {
            "message": "Email sent successfully",
            "recipients": email_data.get("recipients", []),
            "subject": email_data.get("subject", "Test Email")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Simulate real-time updates every 5 seconds
            await asyncio.sleep(5)
            await websocket.send_json({
                "type": "update",
                "timestamp": str(datetime.now()),
                "data": {
                    "connection_status": True,
                    "event": {
                        "id": len(manager.active_connections),
                        "type": "TEST_WEBSOCKET",
                        "description": f"Test WebSocket event at {datetime.now()}"
                    }
                }
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    try:
        print("Starting test server...")
        print("Available endpoints:")
        for route in app.routes:
            print(f"  {route.path} [{', '.join(route.methods) if hasattr(route, 'methods') else 'WebSocket'}]")
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="debug")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()