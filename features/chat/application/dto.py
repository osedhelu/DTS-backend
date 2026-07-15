from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ChatMessageDTO:
    id: int
    order_id: int
    sender_id: int
    sender_role: str
    body: str
    created_at: datetime
