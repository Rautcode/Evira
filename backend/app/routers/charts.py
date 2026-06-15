from fastapi import APIRouter, HTTPException, Body
import matplotlib
matplotlib.use("Agg")  # headless, thread-safe backend for server-side rendering
import matplotlib.pyplot as plt
import os
import uuid
from fastapi.responses import FileResponse
from typing import List, Dict, Any

from app.utils.safe_paths import resolve_within

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
    if chart_type not in ("bar", "line", "pie"):
        raise HTTPException(status_code=400, detail="Invalid chart type")
    if not data:
        raise HTTPException(status_code=400, detail="No data provided for chart")
    # Validate every row contains the requested fields before plotting.
    missing = [i for i, d in enumerate(data) if x_field not in d or y_field not in d]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Rows missing required fields '{x_field}'/'{y_field}': {missing[:10]}",
        )

    os.makedirs(CHARTS_DIR, exist_ok=True)
    file_name = f"chart_{uuid.uuid4()}.png"
    file_path = os.path.join(CHARTS_DIR, file_name)
    x_values = [d[x_field] for d in data]
    y_values = [d[y_field] for d in data]
    fig = plt.figure(figsize=(8, 4))
    try:
        if chart_type == "bar":
            plt.bar(x_values, y_values, color=color)
        elif chart_type == "line":
            plt.plot(x_values, y_values, color=color)
        elif chart_type == "pie":
            plt.pie(y_values, labels=x_values, colors=[color] * len(data))
        plt.title(f"{chart_type.capitalize()} Chart")
        plt.tight_layout()
        plt.savefig(file_path)
    finally:
        plt.close(fig)
    return {"message": "Chart generated", "file": file_name, "download_url": f"/charts/download/{file_name}"}

@router.get("/download/{file_name}")
def download_chart(file_name: str):
    try:
        file_path = resolve_within(CHARTS_DIR, file_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file name")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=os.path.basename(file_path))
