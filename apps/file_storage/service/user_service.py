from typing import List
from ..infra.db.uow import FileStorageUoW
from ..domain.models.user import User
from ..domain.enums.user_role import UserRole
from ..domain.exceptions.auth import UserNotFound, InsufficientPermissions, UserAlreadyExists
from shared.auth.password import password_handler


class UserService:

    def __init__(self, uow: FileStorageUoW):
        self.uow = uow

    async def create_user(self, username: str, password: str, role: UserRole,
                          department: str, current_user: User) -> User:
        if current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
            raise InsufficientPermissions("Only managers and admins can create users")

        async with self.uow:
            existing_user = await self.uow.user_repo.get_by_username(username)
            if existing_user:
                raise UserAlreadyExists("Username already exists")

            hashed_password = password_handler.hash_password(password)
            user = await self.uow.user_repo.create(username, hashed_password, role, department)
            await self.uow.commit()
            return user

    async def get_user_by_id(self, user_id: int, current_user: User) -> User:
        if current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
            raise InsufficientPermissions("Insufficient permissions")

        async with self.uow:
            user = await self.uow.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFound("User not found")

            if current_user.role == UserRole.MANAGER and user.department != current_user.department:
                raise InsufficientPermissions("Can only view users from your department")

            return user

    async def list_users(self, current_user: User) -> List[User]:
        if current_user.role == UserRole.ADMIN:
            async with self.uow:
                return await self.uow.user_repo.get_all()
        elif current_user.role == UserRole.MANAGER:
            async with self.uow:
                return await self.uow.user_repo.get_by_department(current_user.department)
        else:
            raise InsufficientPermissions("Insufficient permissions")

    async def update_user_role(self, user_id: int, new_role: UserRole, current_user: User) -> User:
        if current_user.role != UserRole.ADMIN:
            raise InsufficientPermissions("Only admins can change roles")

        async with self.uow:
            user = await self.uow.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFound("User not found")

            updated_user = await self.uow.user_repo.update_role(user_id, new_role)
            await self.uow.commit()
            return updated_user