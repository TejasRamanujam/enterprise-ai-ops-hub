from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.services.user_service import UserService
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user=Depends(require_role("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.get_all(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.id != user_id and current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Access denied")
    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    service = UserService(db)
    user = await service.update(user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=204)
async def deactivate_user(
    user_id: str,
    current_user=Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    success = await service.deactivate(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
