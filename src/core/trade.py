import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Trade:
    """Represents a single completed trade."""

    price: float
    quantity: int
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    trade_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: float = field(default_factory=time.time)
