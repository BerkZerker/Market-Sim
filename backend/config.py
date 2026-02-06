import json
import os
import secrets
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

_DEFAULT_TICKERS = (
    '{"FUN": 100.0, "MEME": 50.0, "YOLO": 200.0, "HODL": 75.0, "PUMP": 25.0}'
)


@dataclass
class Settings:
    DATABASE_URL: str = field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL", "sqlite+aiosqlite:///./market.db"
        )
    )
    JWT_SECRET: str = field(
        default_factory=lambda: os.environ.get("JWT_SECRET", secrets.token_hex(32))
    )
    JWT_ALGORITHM: str = field(
        default_factory=lambda: os.environ.get("JWT_ALGORITHM", "HS256")
    )
    JWT_EXPIRE_HOURS: int = field(
        default_factory=lambda: int(os.environ.get("JWT_EXPIRE_HOURS", "24"))
    )
    TICKERS: dict[str, float] = field(
        default_factory=lambda: json.loads(os.environ.get("TICKERS", _DEFAULT_TICKERS))
    )
    STARTING_CASH: float = field(
        default_factory=lambda: float(os.environ.get("STARTING_CASH", "10000.0"))
    )
    RATE_LIMIT_REQUESTS: int = field(
        default_factory=lambda: int(os.environ.get("RATE_LIMIT_REQUESTS", "30"))
    )
    RATE_LIMIT_WINDOW: int = field(
        default_factory=lambda: int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
    )
    HOST: str = field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    PORT: int = field(default_factory=lambda: int(os.environ.get("PORT", "8000")))


settings = Settings()
