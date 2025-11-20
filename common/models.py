from dataclasses import dataclass
from typing import Optional

@dataclass
class Message:
    actor: str
    payload: str

@dataclass
class User:
    user_id: str
    username: str
    email: Optional[str] = None
    created_at: Optional[str] = None
