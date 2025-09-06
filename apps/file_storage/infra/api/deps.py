from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.db.connection import AsyncSessionLocal
from ..db.uow import FileStorageUoW
from ...service.auth_service import AuthService
from ...service.user_service import UserService
from ...service.file_service import FileService
from ...domain.models.user import User
from ...domain.exceptions.auth import InvalidCredentials, UserNotFound

security = HTTPBearer()

def get_uow() -> FileStorageUoW:
    return FileStorageUoW(AsyncSessionLocal)

def get_auth_service(uow: FileStorageUoW = Depends(get_uow)) -> AuthService:
    return AuthService(uow)

def get_user_service(uow: FileStorageUoW = Depends(get_uow)) -> UserService:
    return UserService(uow)

def get_file_service(uow: FileStorageUoW = Depends(get_uow)) -> FileService:
    return FileService(uow)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    try:
        return await auth_service.get_current_user(credentials.credentials)
    except (InvalidCredentials, UserNotFound) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )