from dataclasses import dataclass, field
from collections import defaultdict
import uuid

@dataclass
class User:
    """Represents a user or agent in the market."""
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    cash: float = 10000.00
    # defaultdict simplifies portfolio management; avoids KeyError for new stocks.
    portfolio: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))

    def __repr__(self):
        # A cleaner representation for printing user status.
        portfolio_str = ", ".join(f"{ticker}: {qty}" for ticker, qty in self.portfolio.items() if qty > 0)
        return f"User(ID={str(self.user_id)[-4:]}, Cash=${self.cash:,.2f}, Portfolio=[{portfolio_str}])"


