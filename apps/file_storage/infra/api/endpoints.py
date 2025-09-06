from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FileUpload, Form, status
from fastapi.responses import StreamingResponse
from typing import List
from .deps import get_auth_service, get_user_service, get_file_service, get_current_user
from .requests import LoginRequest, CreateUserRequest, UpdateUserRoleRequest
from .responses import *
from ...service.auth_service import AuthService
from ...service.user_service import UserService
from ...service.file_service import FileService
from ...domain.models.user import User
from ...domain.enums.file_visibility import FileVisibility
from ...domain.exceptions.auth import InvalidCredentials, UserNotFound, InsufficientPermissions, UserAlreadyExists
from ...domain.exceptions.file import *

router = APIRouter()

@router.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login(request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        token = await auth_service.login(request.username, request.password)
        return TokenResponse(access_token=token)
    except InvalidCredentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@router.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id, username=current_user.username, role=current_user.role,
        department=current_user.department, created_at=current_user.created_at
    )

@router.post("/users", response_model=UserResponse, tags=["Users"])
async def create_user(request: CreateUserRequest, current_user: User = Depends(get_current_user), user_service: UserService = Depends(get_user_service)):
    try:
        user = await user_service.create_user(request.username, request.password, request.role, request.department, current_user)
        return UserResponse(id=user.id, username=user.username, role=user.role, department=user.department, created_at=user.created_at)
    except InsufficientPermissions as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except UserAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/users", response_model=UserListResponse, tags=["Users"])
async def list_users(current_user: User = Depends(get_current_user), user_service: UserService = Depends(get_user_service)):
    try:
        users = await user_service.list_users(current_user)
        user_responses = [UserResponse(id=user.id, username=user.username, role=user.role, department=user.department, created_at=user.created_at) for user in users]
        return UserListResponse(users=user_responses, count=len(user_responses))
    except InsufficientPermissions as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: int, current_user: User = Depends(get_current_user), user_service: UserService = Depends(get_user_service)):
    try:
        user = await user_service.get_user_by_id(user_id, current_user)
        return UserResponse(id=user.id, username=user.username, role=user.role, department=user.department, created_at=user.created_at)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientPermissions as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.put("/users/{user_id}/role", response_model=UserResponse, tags=["Users"])
async def update_user_role(user_id: int, request: UpdateUserRoleRequest, current_user: User = Depends(get_current_user), user_service: UserService = Depends(get_user_service)):
    try:
        user = await user_service.update_user_role(user_id, request.role, current_user)
        return UserResponse(id=user.id, username=user.username, role=user.role, department=user.department, created_at=user.created_at)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientPermissions as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/files/upload", response_model=FileResponse, tags=["Files"])
async def upload_file(file: UploadFile = FileUpload(...), visibility: FileVisibility = Form(), current_user: User = Depends(get_current_user), file_service: FileService = Depends(get_file_service)):
    try:
        uploaded_file = await file_service.upload_file(file, visibility, current_user)
        return FileResponse(
            id=uploaded_file.id, filename=uploaded_file.filename, original_filename=uploaded_file.original_filename,
            size=uploaded_file.size, content_type=uploaded_file.content_type, visibility=uploaded_file.visibility,
            owner_id=uploaded_file.owner_id, department=uploaded_file.department, download_count=uploaded_file.download_count,
            file_metadata=uploaded_file.file_metadata, created_at=uploaded_file.created_at
        )
    except (FileTypeNotAllowed, FileSizeExceeded, FileAccessDenied, FileUploadFailed) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/files", response_model=FileListResponse, tags=["Files"])
async def list_files(current_user: User = Depends(get_current_user), file_service: FileService = Depends(get_file_service)):
    files = await file_service.get_accessible_files(current_user)
    file_responses = [FileResponse(
        id=file.id, filename=file.filename, original_filename=file.original_filename, size=file.size,
        content_type=file.content_type, visibility=file.visibility, owner_id=file.owner_id,
        department=file.department, download_count=file.download_count, file_metadata=file.file_metadata,
        created_at=file.created_at
    ) for file in files]
    return FileListResponse(files=file_responses, count=len(file_responses))

@router.get("/files/{file_id}", response_model=FileResponse, tags=["Files"])
async def get_file(file_id: int, current_user: User = Depends(get_current_user), file_service: FileService = Depends(get_file_service)):
    try:
        file = await file_service.get_file_by_id(file_id, current_user)
        return FileResponse(
            id=file.id, filename=file.filename, original_filename=file.original_filename, size=file.size,
            content_type=file.content_type, visibility=file.visibility, owner_id=file.owner_id,
            department=file.department, download_count=file.download_count, file_metadata=file.file_metadata,
            created_at=file.created_at
        )
    except FileNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileAccessDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/files/{file_id}/download", tags=["Files"])
async def download_file(file_id: int, current_user: User = Depends(get_current_user),
                        file_service: FileService = Depends(get_file_service)):
    try:
        file_stream, file = await file_service.download_file(file_id, current_user)

        safe_filename = file.original_filename.encode('ascii', 'ignore').decode('ascii')
        if not safe_filename:
            safe_filename = f"file_{file.id}"

        return StreamingResponse(
            file_stream,
            media_type=file.content_type,
            headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
        )
    except FileNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileAccessDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete("/files/{file_id}", response_model=MessageResponse, tags=["Files"])
async def delete_file(file_id: int, current_user: User = Depends(get_current_user), file_service: FileService = Depends(get_file_service)):
    try:
        await file_service.delete_file(file_id, current_user)
        return MessageResponse(message="File deleted successfully")
    except FileNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileAccessDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))