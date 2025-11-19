from dataclasses import dataclass

@dataclass
class Message:
    actor: str
    payload: str

