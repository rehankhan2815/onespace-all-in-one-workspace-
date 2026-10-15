import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings


def get_upload_dir() -> Path:
    """Get the upload directory, creating it if it doesn't exist."""
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def generate_storage_name(original_filename: str) -> str:
    """Generate a unique storage filename while preserving the extension."""
    ext = Path(original_filename).suffix
    unique_id = uuid.uuid4().hex
    return f"{unique_id}{ext}"


def get_storage_path(storage_name: str) -> Path:
    """Get the full storage path for a given storage name."""
    return get_upload_dir() / storage_name


def save_upload_file(file: BinaryIO, storage_name: str) -> int:
    """Save an uploaded file to storage and return its size in bytes."""
    storage_path = get_storage_path(storage_name)
    with storage_path.open("wb") as buffer:
        shutil.copyfileobj(file, buffer)
    return storage_path.stat().st_size


def delete_storage_file(storage_name: str) -> bool:
    """Delete a file from storage. Returns True if file existed and was deleted."""
    storage_path = get_storage_path(storage_name)
    try:
        storage_path.unlink()
        return True
    except FileNotFoundError:
        return False


def get_file_size(storage_name: str) -> int | None:
    """Get the size of a stored file in bytes, or None if not found."""
    storage_path = get_storage_path(storage_name)
    try:
        return storage_path.stat().st_size
    except FileNotFoundError:
        return None


def validate_upload_size(file_size: int) -> None:
    """Validate that the upload size is within limits."""
    if file_size > settings.max_upload_size:
        max_mb = settings.max_upload_size / (1024 * 1024)
        raise ValueError(f"File size exceeds maximum allowed size of {max_mb:.0f} MB")


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe storage and display."""
    # Remove path components
    filename = os.path.basename(filename)
    # Limit length
    if len(filename) > 500:
        ext = Path(filename).suffix
        filename = filename[:500 - len(ext)] + ext
    return filename


def is_descendant(ancestor_id: uuid.UUID, descendant_id: uuid.UUID, db_session) -> bool:
    """Check if a folder is a descendant of another folder (including self)."""
    if ancestor_id == descendant_id:
        return True

    current_id = descendant_id
    while current_id is not None:
        if current_id == ancestor_id:
            return True
        # Query parent
        from app.models.folder import Folder
        folder = db_session.get(Folder, current_id)
        if folder is None:
            break
        current_id = folder.parent_id

    return False
