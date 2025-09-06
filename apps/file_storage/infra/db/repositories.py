from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from .models import UserModel, FileModel
from ...domain.models.user import User
from ...domain.models.file import File
from ...domain.enums.user_role import UserRole
from ...domain.enums.file_visibility import FileVisibility


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, username: str, hashed_password: str, role: UserRole, department: str) -> User:
        user_model = UserModel(
            username=username,
            hashed_password=hashed_password,
            role=role,
            department=department
        )
        self.session.add(user_model)
        await self.session.flush()
        await self.session.refresh(user_model)
        return self._to_domain(user_model)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        user_model = result.scalar_one_or_none()
        return self._to_domain(user_model) if user_model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(select(UserModel).where(UserModel.username == username))
        user_model = result.scalar_one_or_none()

        return self._to_domain(user_model) if user_model else None

    async def get_by_department(self, department: str) -> List[User]:
        result = await self.session.execute(select(UserModel).where(UserModel.department == department))
        return [self._to_domain(model) for model in result.scalars().all()]

    async def get_all(self) -> List[User]:
        result = await self.session.execute(select(UserModel))
        return [self._to_domain(model) for model in result.scalars().all()]

    async def update_role(self, user_id: int, role: UserRole) -> User:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        user_model = result.scalar_one()
        user_model.role = role
        await self.session.flush()
        await self.session.refresh(user_model)
        return self._to_domain(user_model)

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            role=model.role,
            department=model.department,
            created_at=model.created_at,
            hashed_password=model.hashed_password
        )


class FileRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, filename: str, original_filename: str, size: int,
                     content_type: str, visibility: FileVisibility, s3_path: str,
                     owner_id: int, department: str) -> File:
        file_model = FileModel(
            filename=filename,
            original_filename=original_filename,
            size=size,
            content_type=content_type,
            visibility=visibility,
            s3_path=s3_path,
            owner_id=owner_id,
            department=department
        )
        self.session.add(file_model)
        await self.session.flush()
        await self.session.refresh(file_model)
        return self._to_domain(file_model)

    async def get_by_id(self, file_id: int) -> Optional[File]:
        result = await self.session.execute(select(FileModel).where(FileModel.id == file_id))
        file_model = result.scalar_one_or_none()
        return self._to_domain(file_model) if file_model else None

    async def get_accessible_files(self, user_id: int, user_role: UserRole, user_department: str) -> List[File]:
        conditions = []

        if user_role == UserRole.ADMIN:
            conditions.append(True)
        elif user_role == UserRole.MANAGER:
            conditions.extend([
                FileModel.visibility == FileVisibility.PUBLIC,
                FileModel.visibility == FileVisibility.DEPARTMENT,
                and_(FileModel.visibility == FileVisibility.PRIVATE, FileModel.owner_id == user_id)
            ])
        else:
            conditions.extend([
                FileModel.visibility == FileVisibility.PUBLIC,
                and_(FileModel.visibility == FileVisibility.DEPARTMENT, FileModel.department == user_department),
                and_(FileModel.visibility == FileVisibility.PRIVATE, FileModel.owner_id == user_id)
            ])

        result = await self.session.execute(select(FileModel).where(or_(*conditions)))
        return [self._to_domain(model) for model in result.scalars().all()]

    async def update_metadata(self, file_id: int, metadata: dict) -> None:
        result = await self.session.execute(select(FileModel).where(FileModel.id == file_id))
        file_model = result.scalar_one_or_none()
        if file_model:
            file_model.file_metadata = metadata
            await self.session.flush()

    async def increment_download_count(self, file_id: int) -> None:
        result = await self.session.execute(select(FileModel).where(FileModel.id == file_id))
        file_model = result.scalar_one_or_none()
        if file_model:
            file_model.download_count += 1
            await self.session.flush()

    async def delete(self, file_id: int) -> None:
        result = await self.session.execute(select(FileModel).where(FileModel.id == file_id))
        file_model = result.scalar_one_or_none()
        if file_model:
            await self.session.delete(file_model)
            await self.session.flush()

    def _to_domain(self, model: FileModel) -> File:
        return File(
            id=model.id,
            filename=model.filename,
            original_filename=model.original_filename,
            size=model.size,
            content_type=model.content_type,
            visibility=model.visibility,
            s3_path=model.s3_path,
            owner_id=model.owner_id,
            department=model.department,
            download_count=model.download_count,
            created_at=model.created_at,
            file_metadata=model.file_metadata
        )