from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.db.base import Base
from ...domain.enums.user_role import UserRole
from ...domain.enums.file_visibility import FileVisibility


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    department = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    files = relationship("FileModel", back_populates="owner")


class FileModel(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    size = Column(BigInteger, nullable=False)
    content_type = Column(String(100), nullable=False)
    visibility = Column(Enum(FileVisibility), nullable=False)
    s3_path = Column(String(500), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department = Column(String(100), nullable=False)
    download_count = Column(Integer, default=0)
    file_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("UserModel", back_populates="files")