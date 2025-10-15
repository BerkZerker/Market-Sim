import uuid
import time
from dataclasses import dataclass, field

@dataclass(order=True)
class Order:
    """Represents a single order in the order book."""
    
    # --- Primary Sorting Key ---
    price: float = field(compare=True) # Price of the order
    
    # --- Secondary Sorting Key (for price-time priority) ---
    timestamp: float = field(default_factory=time.time, compare=True)
    
    # --- Order Data (not used for sorting) ---
    quantity: int = field(compare=False) # Number of shares
    user_id: uuid.UUID = field(compare=False) # The ID of the agent who placed the order
    order_id: uuid.UUID = field(default_factory=uuid.uuid4, compare=False) # Unique ID for this specific order
    
    # Note: We don't include 'side' (buy/sell) here because bids and asks
    # will be stored in separate lists in the OrderBook.