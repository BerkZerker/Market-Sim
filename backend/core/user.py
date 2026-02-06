import uuid
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class User:
    """Represents a user or agent in the market."""

    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    username: str = ""
    cash: float = 10000.00
    portfolio: defaultdict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    is_market_maker: bool = False

    def __repr__(self):
        portfolio_str = ", ".join(
            f"{ticker}: {qty}" for ticker, qty in self.portfolio.items() if qty > 0
        )
        return (
            f"User(ID={str(self.user_id)[-4:]}, "
            f"Cash=${self.cash:,.2f}, "
            f"Portfolio=[{portfolio_str}])"
        )
