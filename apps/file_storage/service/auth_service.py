from ..infra.db.uow import FileStorageUoW
from ..domain.models.user import User
from ..domain.exceptions.auth import InvalidCredentials, UserNotFound
from shared.auth.jwt_handler import jwt_handler
from shared.auth.password import password_handler


class AuthService:

    def __init__(self, uow: FileStorageUoW):
        self.uow = uow

    async def login(self, username: str, password: str) -> str:
        print(f"Login attempt: {username}")
        async with self.uow:
            user = await self.uow.user_repo.get_by_username(username)
            print(f"User found: {user is not None}")
            if user:
                print(f"Password check: {password_handler.verify_password(password, user.hashed_password)}")
            if not user or not password_handler.verify_password(password, user.hashed_password):
                raise InvalidCredentials("Invalid username or password")

            return jwt_handler.create_token({"sub": user.username})
    async def get_current_user(self, token: str) -> User:
        try:
            payload = jwt_handler.decode_token(token)
            username = payload.get("sub")
            if not username:
                raise InvalidCredentials("Invalid token")

            async with self.uow:
                user = await self.uow.user_repo.get_by_username(username)
                if not user:
                    raise UserNotFound("User not found")

                return user
        except ValueError:
            raise InvalidCredentials("Invalid token")