from shared.db.uow import SQLAlchemyUoW
from .repositories import UserRepository, FileRepository


class FileStorageUoW(SQLAlchemyUoW):

    async def __aenter__(self):
        await super().__aenter__()
        self.user_repo = UserRepository(self.session)
        self.file_repo = FileRepository(self.session)
        return self