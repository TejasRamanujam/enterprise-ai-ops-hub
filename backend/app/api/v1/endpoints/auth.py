from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import structlog

from app.core.database import get_db
from app.core.security import (
    create_access_token, create_refresh_token, decode_token,
    get_current_user, settings
)
from app.services.user_service import UserService
from app.services.audit_service import AuditService
from app.schemas.user import (
    UserCreate, UserLogin, TokenResponse, UserResponse,
    RefreshTokenRequest, ChangePasswordRequest
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = structlog.get_logger()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    if await service.get_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await service.get_by_username(user_data.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    user = await service.create(user_data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    audit = AuditService(db)
    user = await service.authenticate(credentials.email, credentials.password)
    if not user:
        await audit.log(
            action="login_failed",
            resource_type="user",
            details={"email": credentials.email},
            ip_address=request.client.host,
            status="failure",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(
        subject=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(subject=user.id, role=user.role)
    await audit.log(
        action="login_success",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        ip_address=request.client.host,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    service = UserService(db)
    user = await service.get_by_id(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    access_token = create_access_token(subject=user.id, role=user.role)
    new_refresh = create_refresh_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return current_user


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    success = await service.change_password(
        current_user.id, body.current_password, body.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    return {"message": "Password changed successfully"}
