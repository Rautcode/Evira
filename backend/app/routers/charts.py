from fastapi import APIRouter, HTTPException, Body
import matplotlib.pyplot as plt
import os
import uuid
from fastapi.responses import FileResponse
from typing import List, Dict, Any

router = APIRouter(tags=["charts"], prefix="/charts")
CHARTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../charts'))

@router.post("/generate")
def generate_chart(
    data: List[Dict[str, Any]] = Body(...),
    chart_type: str = Body("bar"),
    x_field: str = Body("name"),
    y_field: str = Body("value"),
    color: str = Body("#1E88E5")
):
    if not os.path.exists(CHARTS_DIR):
        os.makedirs(CHARTS_DIR)
    file_id = str(uuid.uuid4())
    file_name = f"chart_{file_id}.png"
    file_path = os.path.join(CHARTS_DIR, file_name)
    plt.figure(figsize=(8,4))
    if chart_type == "bar":
        plt.bar([d[x_field] for d in data], [d[y_field] for d in data], color=color)
    elif chart_type == "line":
        plt.plot([d[x_field] for d in data], [d[y_field] for d in data], color=color)
    elif chart_type == "pie":
        plt.pie([d[y_field] for d in data], labels=[d[x_field] for d in data], colors=[color]*len(data))
    else:
        raise HTTPException(status_code=400, detail="Invalid chart type")
    plt.title(f"{chart_type.capitalize()} Chart")
    plt.tight_layout()
    plt.savefig(file_path)
    plt.close()
    return {"message": "Chart generated", "file": file_name, "download_url": f"/charts/download/{file_name}"}

@router.get("/download/{file_name}")
def download_chart(file_name: str):
    file_path = os.path.join(CHARTS_DIR, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=file_name)
