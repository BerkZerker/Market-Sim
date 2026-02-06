from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
from config import settings
from core.user import User
from db.crud import get_user_by_api_key, get_user_by_id
from db.database import get_session
from engine.exchange import Exchange
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Singleton exchange — set in main.py lifespan
_exchange: Exchange | None = None


def set_exchange(exchange: Exchange):
    global _exchange
    _exchange = exchange


def get_exchange() -> Exchange:
    if _exchange is None:
        raise RuntimeError("Exchange not initialized")
    return _exchange


async def get_db():
    async for session in get_session():
        yield session


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


async def get_current_user(
    authorization: str | None = Header(None),
    x_api_key: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
    exchange: Exchange = Depends(get_exchange),
) -> User:
    user_id: str | None = None

    # Try JWT first
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        user_id = decode_jwt(token)

    # Fall back to API key
    if user_id is None and x_api_key:
        db_user = await get_user_by_api_key(db, x_api_key)
        if db_user:
            user_id = db_user.id

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication",
        )

    # Get in-memory user from exchange
    mem_user = exchange.get_user(UUID(user_id))
    if mem_user is None:
        # Try loading from DB
        db_user = await get_user_by_id(db, user_id)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User not loaded in exchange",
        )

    return mem_user
