from pydantic import BaseModel
from ...domain.enums.user_role import UserRole
from ...domain.enums.file_visibility import FileVisibility

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: UserRole
    department: str

class UpdateUserRoleRequest(BaseModel):
    role: UserRole

class FileUploadRequest(BaseModel):
    visibility: FileVisibility