"""
Configuration management for FTP upload system.
Loads and validates environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://prod.fotosfolio.com")
    API_UPLOADS_BASE_URL: str = os.getenv(
        "API_UPLOADS_BASE_URL", "https://api.fotosfolio.com"
    )
    API_ZIP_BASE_URL: str = os.getenv(
        "API_ZIP_BASE_URL", "https://zip.fotosfolio.com"
    )
    API_AUTH_TOKEN: str = os.getenv("API_AUTH_TOKEN", "")
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))

    # Object Storage Configuration
    # Note: Uploads use presigned URLs from backend API (no direct S3 credentials needed)
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")

    # FTP Configuration
    FTP_ROOT_DIR: Path = Path(os.getenv("FTP_ROOT_DIR", "/ftp_root"))

    # Processing Configuration
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))
    MAX_CONCURRENT_UPLOADS: int = int(os.getenv("MAX_CONCURRENT_UPLOADS", "4"))
    BATCH_TIMEOUT_SECONDS: int = int(os.getenv("BATCH_TIMEOUT_SECONDS", "30"))

    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_MULTIPLIER: float = float(os.getenv("RETRY_BACKOFF_MULTIPLIER", "2"))
    RETRY_INITIAL_DELAY: float = float(os.getenv("RETRY_INITIAL_DELAY", "1"))

    # Upload Configuration
    UPLOAD_CHUNK_SIZE: int = int(os.getenv("UPLOAD_CHUNK_SIZE", "1048576"))  # 1MB

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "ftp_processor.log")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        errors = []

        if not cls.API_AUTH_TOKEN:
            errors.append("API_AUTH_TOKEN is required")

        if not cls.FTP_ROOT_DIR.exists():
            errors.append(f"FTP_ROOT_DIR does not exist: {cls.FTP_ROOT_DIR}")

        if cls.BATCH_SIZE < 1:
            errors.append("BATCH_SIZE must be at least 1")

        if cls.MAX_CONCURRENT_UPLOADS < 1:
            errors.append("MAX_CONCURRENT_UPLOADS must be at least 1")

        if errors:
            raise ValueError(
                f"Configuration validation failed:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

    @classmethod
    def display(cls) -> str:
        """Return a string representation of the configuration (hiding secrets)."""
        return f"""
Configuration:
  API Base URL: {cls.API_BASE_URL}
  API Uploads Base URL: {cls.API_UPLOADS_BASE_URL}
  API Auth Token: {"*" * 20 if cls.API_AUTH_TOKEN else "NOT SET"}
  API Timeout: {cls.API_TIMEOUT}s

  S3 Bucket: {cls.S3_BUCKET_NAME or "Not configured"}
  Note: Using presigned URLs from backend API (no direct S3 credentials)

  FTP Root Dir: {cls.FTP_ROOT_DIR}

  Batch Size: {cls.BATCH_SIZE}
  Max Concurrent Uploads: {cls.MAX_CONCURRENT_UPLOADS}
  Batch Timeout: {cls.BATCH_TIMEOUT_SECONDS}s

  Max Retries: {cls.MAX_RETRIES}
  Retry Backoff: {cls.RETRY_BACKOFF_MULTIPLIER}x
  Initial Delay: {cls.RETRY_INITIAL_DELAY}s

  Upload Chunk Size: {cls.UPLOAD_CHUNK_SIZE / 1024 / 1024:.1f}MB

  Log Level: {cls.LOG_LEVEL}
  Log File: {cls.LOG_FILE}
"""


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    # Don't fail on import, but warn
    import warnings

    warnings.warn(f"Configuration validation failed: {e}")
