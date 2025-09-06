from typing import List, Tuple
from fastapi import UploadFile
import uuid
from ..infra.db.uow import FileStorageUoW
from ..domain.models.user import User
from ..domain.models.file import File
from ..domain.enums.user_role import UserRole
from ..domain.enums.file_visibility import FileVisibility
from ..domain.exceptions.file import *
from shared.storage.minio_client import minio_client


class FileService:
    FILE_TYPE_LIMITS = {
        UserRole.USER: {"pdf"},
        UserRole.MANAGER: {"pdf", "doc", "docx"},
        UserRole.ADMIN: {"pdf", "doc", "docx"}
    }

    SIZE_LIMITS = {
        UserRole.USER: 10 * 1024 * 1024,
        UserRole.MANAGER: 50 * 1024 * 1024,
        UserRole.ADMIN: 100 * 1024 * 1024
    }

    VISIBILITY_PERMISSIONS = {
        UserRole.USER: {FileVisibility.PRIVATE},
        UserRole.MANAGER: {FileVisibility.PRIVATE, FileVisibility.DEPARTMENT, FileVisibility.PUBLIC},
        UserRole.ADMIN: {FileVisibility.PRIVATE, FileVisibility.DEPARTMENT, FileVisibility.PUBLIC}
    }

    def __init__(self, uow: FileStorageUoW):
        self.uow = uow

    async def upload_file(self, file: UploadFile, visibility: FileVisibility, user: User) -> File:
        file_ext = file.filename.split('.')[-1].lower()

        if file_ext not in self.FILE_TYPE_LIMITS[user.role]:
            raise FileTypeNotAllowed(f"File type .{file_ext} not allowed for your role")

        if file.size > self.SIZE_LIMITS[user.role]:
            raise FileSizeExceeded(f"File size exceeds limit for your role")

        if visibility not in self.VISIBILITY_PERMISSIONS[user.role]:
            raise FileAccessDenied(f"You cannot create {visibility.value} files")

        file_id = str(uuid.uuid4())
        s3_path = f"{user.department}/{file_id}.{file_ext}"

        try:
            minio_client.upload_file(s3_path, file.file, file.content_type, file.size)
        except Exception as e:
            raise FileUploadFailed(f"File upload failed: {e}")

        async with self.uow:
            db_file = await self.uow.file_repo.create(
                filename=f"{file_id}.{file_ext}",
                original_filename=file.filename,
                size=file.size,
                content_type=file.content_type,
                visibility=visibility,
                s3_path=s3_path,
                owner_id=user.id,
                department=user.department
            )
            await self.uow.commit()

        from ..worker.tasks import extract_metadata
        extract_metadata.delay(db_file.id)

        return db_file

    async def get_accessible_files(self, user: User) -> List[File]:
        async with self.uow:
            return await self.uow.file_repo.get_accessible_files(user.id, user.role, user.department)

    async def get_file_by_id(self, file_id: int, user: User) -> File:
        async with self.uow:
            file = await self.uow.file_repo.get_by_id(file_id)
            if not file:
                raise FileNotFound("File not found")

            if not self._check_file_access(file, user):
                raise FileAccessDenied("Access denied")

            return file

    async def download_file(self, file_id: int, user: User) -> Tuple[any, File]:
        file = await self.get_file_by_id(file_id, user)

        async with self.uow:
            await self.uow.file_repo.increment_download_count(file_id)
            await self.uow.commit()

        file_stream = minio_client.download_file(file.s3_path)
        return file_stream, file

    async def delete_file(self, file_id: int, user: User) -> None:
        file = await self.get_file_by_id(file_id, user)

        can_delete = (
                user.role == UserRole.ADMIN or
                file.owner_id == user.id or
                (user.role == UserRole.MANAGER and file.department == user.department)
        )

        if not can_delete:
            raise FileAccessDenied("Cannot delete this file")

        async with self.uow:
            await self.uow.file_repo.delete(file_id)
            await self.uow.commit()

        minio_client.delete_file(file.s3_path)

    def _check_file_access(self, file: File, user: User) -> bool:
        if user.role == UserRole.ADMIN:
            return True

        if file.visibility == FileVisibility.PUBLIC:
            return True

        if file.visibility == FileVisibility.DEPARTMENT:
            return user.role == UserRole.MANAGER or file.department == user.department

        if file.visibility == FileVisibility.PRIVATE:
            return file.owner_id == user.id

        return False