from uuid import UUID

from api.dependencies import (
    create_jwt,
    get_db,
    get_exchange,
    hash_password,
    verify_password,
)
from config import settings
from core.user import User
from db.crud import create_user, get_user_by_username
from engine.exchange import Exchange
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str


class RegisterResponse(BaseModel):
    user_id: str
    username: str
    api_key: str
    jwt_token: str
    cash: float


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: str
    username: str
    jwt_token: str


@router.post("/register", response_model=RegisterResponse)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    exchange: Exchange = Depends(get_exchange),
):
    if len(req.username) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 2 characters",
        )
    if len(req.password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters",
        )

    existing = await get_user_by_username(db, req.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    pw_hash = hash_password(req.password)
    db_user = await create_user(db, req.username, pw_hash)
    await db.commit()

    # Create in-memory user and register with exchange
    mem_user = User(
        user_id=UUID(db_user.id),
        username=db_user.username,
        cash=settings.STARTING_CASH,
    )
    exchange.register_user(mem_user)

    token = create_jwt(db_user.id)
    return RegisterResponse(
        user_id=db_user.id,
        username=db_user.username,
        api_key=db_user.api_key,
        jwt_token=token,
        cash=mem_user.cash,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    db_user = await get_user_by_username(db, req.username)
    if not db_user or not verify_password(req.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_jwt(db_user.id)
    return LoginResponse(
        user_id=db_user.id,
        username=db_user.username,
        jwt_token=token,
    )
