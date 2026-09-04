class OverwatchRule:
    def __init__(self, target_text: str, auto_click: bool, require_focus: bool, pattern: str = "exact"):
        self.target_text = target_text
        self.auto_click = auto_click
        self.require_focus = require_focus
        self.pattern = pattern
        
    def matches(self, text: str) -> bool:
        if not text:
            return False
        if self.pattern == "exact":
            return self.target_text.lower() == text.lower()
        elif self.pattern == "contains":
            return self.target_text.lower() in text.lower()
        return False
