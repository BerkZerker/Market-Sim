import time
import uuid
from dataclasses import dataclass, field


@dataclass(order=True)
class Order:
    """
    Represents a single order in the order book.
    The `order=True` argument automatically makes the class sortable
    based on the order of its fields.
    """

    # Primary sorting key
    price: float = field(compare=True)

    # Other fields
    quantity: int = field(compare=False)
    user_id: uuid.UUID = field(compare=False)
    timestamp: float = field(default_factory=time.time, compare=True)
    order_id: uuid.UUID = field(default_factory=uuid.uuid4, compare=False)
