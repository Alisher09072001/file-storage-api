from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from ..enums.file_visibility import FileVisibility

@dataclass
class File:
    id: int
    filename: str
    original_filename: str
    size: int
    content_type: str
    visibility: FileVisibility
    s3_path: str
    owner_id: int
    department: str
    download_count: int
    created_at: datetime
    file_metadata: Optional[Dict[str, Any]] = None