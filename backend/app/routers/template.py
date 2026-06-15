from fastapi import APIRouter, HTTPException, Body
from app.services.template_service import TemplateService
from typing import Dict, Any
import uuid

router = APIRouter(tags=["template"], prefix="/template")
template_service = TemplateService()

@router.get("")
@router.get("/")
def list_templates():
    # Return directly list of templates as frontend expects an array in res.data
    return template_service.list_templates()

@router.get("/{template_id}")
def get_template(template_id: str):
    try:
        return template_service.load_template(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template id")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

@router.post("")
@router.post("/")
def create_template(data: Dict[str, Any] = Body(...)):
    template_id = data.get("id") or str(uuid.uuid4())
    data["id"] = template_id
    try:
        template_service.save_template(template_id, data)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template id")
    return {"message": "Template created", "id": template_id}

@router.put("/{template_id}")
def edit_template(template_id: str, updates: Dict[str, Any] = Body(...)):
    try:
        template_service.edit_template(template_id, updates)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template id")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template updated"}

@router.delete("/{template_id}")
def delete_template(template_id: str):
    try:
        template_service.delete_template(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template id")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted"}

@router.post("/preview/{template_id}")
def preview_template(template_id: str, context: Dict[str, Any] = Body(...)):
    try:
        preview = template_service.preview_template(template_id, context)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template id")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"preview": preview}
