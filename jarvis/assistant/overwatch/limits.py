import time

class RateLimiter:
    def __init__(self, max_actions=5, interval=10.0):
        self.max_actions = max_actions
        self.interval = interval
        self.actions = []
        
    def allow(self) -> bool:
        now = time.time()
        self.actions = [t for t in self.actions if now - t < self.interval]
        if len(self.actions) < self.max_actions:
            self.actions.append(now)
            return True
        return False
