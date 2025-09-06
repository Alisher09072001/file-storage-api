from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ..enums.user_role import UserRole

@dataclass
class User:
    id: int
    username: str
    role: UserRole
    department: str
    created_at: datetime
    hashed_password: Optional[str] = None