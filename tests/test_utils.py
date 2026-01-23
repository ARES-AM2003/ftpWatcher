"""
Unit tests for utility functions.
"""

import pytest
from pathlib import Path
from utils import (
    parse_ftp_path,
    get_mime_type,
    generate_file_key,
    format_bytes
)


def test_parse_ftp_path():
    """Test FTP path parsing."""
    ftp_root = Path("/ftp_root")
    
    # Valid path
    file_path = Path("/ftp_root/john_123/ftp/camera1/test.jpg")
    result = parse_ftp_path(file_path, ftp_root)
    
    assert result is not None
    username_userid, user_id, ftp_username = result
    assert username_userid == "john_123"
    assert user_id == "123"
    assert ftp_username == "camera1"
    
    # Invalid path (missing ftp folder)
    file_path = Path("/ftp_root/john_123/uploads/test.jpg")
    result = parse_ftp_path(file_path, ftp_root)
    assert result is None
    
    # Invalid path (no underscore in username_userid)
    file_path = Path("/ftp_root/john/ftp/camera1/test.jpg")
    result = parse_ftp_path(file_path, ftp_root)
    assert result is None


def test_get_mime_type():
    """Test MIME type detection."""
    assert get_mime_type(Path("test.jpg")) == "image/jpeg"
    assert get_mime_type(Path("test.png")) == "image/png"
    assert get_mime_type(Path("test.mp4")) == "video/mp4"
    assert get_mime_type(Path("test.unknown")) == "application/octet-stream"


def test_generate_file_key():
    """Test S3 file key generation."""
    key = generate_file_key("john_123", "camera1", "test.jpg")
    assert key == "john_123/ftp/camera1/test.jpg"


def test_format_bytes():
    """Test byte formatting."""
    assert format_bytes(500) == "500.00 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(1024 * 1024) == "1.00 MB"
    assert format_bytes(1024 * 1024 * 1024) == "1.00 GB"
