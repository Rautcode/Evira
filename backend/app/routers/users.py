"""User management API (admin-only)."""

from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import Optional

from app.core.security import require_role
from app.services.user_service import list_users, create_user, update_user, delete_user

router = APIRouter(tags=["users"], prefix="/users")
_admin = Depends(require_role("admin"))

VALID_ROLES = {"operator", "engineer", "admin"}


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "operator"


class UpdateUserRequest(BaseModel):
    role: str
    active: bool = True
    password: Optional[str] = None


@router.get("", dependencies=[_admin])
def get_users():
    return list_users()


@router.post("", dependencies=[_admin])
def post_user(data: CreateUserRequest = Body(...)):
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
    if not data.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    try:
        new_id = create_user(data.username.strip(), data.password, data.role)
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="Username already exists")
        raise HTTPException(status_code=500, detail="Failed to create user")
    return {"message": "User created", "id": new_id}


@router.put("/{user_id}", dependencies=[_admin])
def put_user(user_id: int, data: UpdateUserRequest = Body(...)):
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
    ok = update_user(user_id, {"role": data.role, "active": data.active, "password": data.password})
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated"}


@router.delete("/{user_id}", dependencies=[_admin])
def deactivate_user(user_id: int):
    ok = delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deactivated"}
