"""
Utility functions for FTP upload system.
"""

import hashlib
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

from logger import get_logger

logger = get_logger(__name__)


def parse_ftp_path(file_path: Path, ftp_root: Path) -> Optional[Tuple[str, str, str]]:
    """
    Parse FTP file path to extract user information.

    Expected structure: {ftp_root}/username_userid/ftp/ftpusername/filename

    Args:
        file_path: Full path to the uploaded file
        ftp_root: FTP root directory

    Returns:
        Tuple of (username_userid, user_id, ftp_username) or None if invalid
    """
    try:
        # Get relative path from FTP root
        rel_path = file_path.relative_to(ftp_root)
        parts = rel_path.parts

        if len(parts) < 4:
            logger.warning(f"Invalid FTP path structure: {file_path}")
            return None

        # Extract components
        username_userid = parts[0]  # e.g., "john_123"
        ftp_folder = parts[1]  # Should be "ftp"
        ftp_username = parts[2]  # e.g., "camera1"

        if ftp_folder != "ftp":
            logger.warning(
                f"Expected 'ftp' folder in path, got '{ftp_folder}': {file_path}"
            )
            return None

        # Extract user_id from username_userid
        if "_" not in username_userid:
            logger.warning(
                f"Invalid username_userid format (expected 'username_userid'): {username_userid}"
            )
            return None

        user_id = username_userid.split("_")[-1]

        return username_userid, user_id, ftp_username

    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing FTP path {file_path}: {e}")
        return None


def get_mime_type(file_path: Path) -> str:
    """
    Detect MIME type of a file.

    Args:
        file_path: Path to the file

    Returns:
        MIME type string (defaults to 'application/octet-stream')
    """
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "application/octet-stream"


def get_file_size(file_path: Path) -> int:
    """
    Get file size in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes
    """
    return file_path.stat().st_size


def generate_file_id() -> str:
    """
    Generate a unique file ID.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def generate_file_key(username_userid: str, ftp_username: str, filename: str) -> str:
    """
    Generate S3 object key for a file.

    Format: Original/username_userid/ftp/ftpusername/filename

    Args:
        username_userid: Combined username and user ID
        ftp_username: FTP username (e.g., camera name)
        filename: Original filename

    Returns:
        S3 object key
    """
    return f"Original/{username_userid}/ftp/{ftp_username}/{filename}"


def calculate_file_hash(file_path: Path, algorithm: str = "md5") -> str:
    """
    Calculate hash of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm ('md5', 'sha256', etc.)

    Returns:
        Hex digest of the file hash
    """
    hash_obj = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def safe_delete_file(file_path: Path) -> bool:
    """
    Safely delete a file with error handling.

    Args:
        file_path: Path to the file to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        if file_path.exists():
            # Check if file is still being written (size might change)
            try:
                initial_size = file_path.stat().st_size
                # Small delay to check if file is stable
                import time

                time.sleep(0.1)
                if file_path.stat().st_size != initial_size:
                    logger.warning(
                        f"File size changed during deletion check, skipping: {file_path}"
                    )
                    return False
            except OSError:
                pass  # File might have been deleted already

            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
            return True
        else:
            logger.warning(f"File does not exist, cannot delete: {file_path}")
            return False
    except PermissionError as e:
        logger.error(f"Permission denied when deleting file {file_path}: {e}")
        return False
    except OSError as e:
        logger.error(f"OS error deleting file {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting file {file_path}: {e}")
        return False


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes into human-readable string.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path
    """
    path.mkdir(parents=True, exist_ok=True)
