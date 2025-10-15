

class OrderBook:
    
    def __init__(self):
        self.bids = {} # UID, value, num_shares
        self.asks = {}

    
    def make_bid(self, uid: str, value: float, num_shares: int):
        if uid in self.bids:
            raise ValueError("Bid with this UID already exists.")
        self.bids[uid] = (value, num_shares)
