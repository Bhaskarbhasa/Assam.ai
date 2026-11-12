"""
Session Memory & Multi-Turn Context Manager.
Maintains conversational history and caches hardware specifications
to resolve follow-ups efficiently and prevent redundant tool executions.
"""
from typing import List, Dict, Any, Optional

class ConversationSession:
    def __init__(self, session_id: str = "default_session"):
        self.session_id = session_id
        self.history: List[Dict[str, str]] = []  # [{"role": "user"|"assistant", "content": "..."}]
        self.hardware_cache: Dict[str, Any] = {}  # Cached tool outputs: "cpu", "memory", "storage", "gpu"

    def add_user_message(self, message: str):
        self.history.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str, tool_used: Optional[str] = None):
        self.history.append({
            "role": "assistant", 
            "content": message,
            "tool_used": tool_used
        })

    def update_hardware_cache(self, category: str, data: Dict[str, Any]):
        self.hardware_cache[category] = data

    def get_cached_spec(self, category: str) -> Optional[Dict[str, Any]]:
        return self.hardware_cache.get(category)

    def clear(self):
        self.history.clear()
        self.hardware_cache.clear()

session_context = ConversationSession()
