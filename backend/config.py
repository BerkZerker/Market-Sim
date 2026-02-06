import os
import secrets
from dataclasses import dataclass, field


@dataclass
class Settings:
    DATABASE_URL: str = "sqlite+aiosqlite:///./market.db"
    JWT_SECRET: str = field(
        default_factory=lambda: os.environ.get("JWT_SECRET", secrets.token_hex(32))
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    TICKERS: dict[str, float] = field(
        default_factory=lambda: {
            "FUN": 100.0,
            "MEME": 50.0,
            "YOLO": 200.0,
            "HODL": 75.0,
            "PUMP": 25.0,
        }
    )
    STARTING_CASH: float = 10000.0


settings = Settings()
