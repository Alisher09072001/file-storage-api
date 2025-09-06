from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional, List
from ...domain.enums.user_role import UserRole
from ...domain.enums.file_visibility import FileVisibility


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    department: str
    created_at: datetime

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    size: int
    content_type: str
    visibility: FileVisibility
    owner_id: int
    department: str
    download_count: int
    file_metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


class FileListResponse(BaseModel):
    files: List[FileResponse]
    count: int


class UserListResponse(BaseModel):
    users: List[UserResponse]
    count: int