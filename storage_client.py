"""
Storage client for S3-compatible object storage.
Handles streaming uploads with retry logic and concurrency control.
"""

import asyncio
from pathlib import Path
from typing import Optional

import aiofiles
import aiohttp

from config import Config
from logger import get_logger
from utils import format_bytes, get_mime_type

logger = get_logger(__name__)


class StorageClient:
    """Async client for S3-compatible object storage uploads."""

    def __init__(self):
        self.chunk_size = Config.UPLOAD_CHUNK_SIZE
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Create aiohttp session on context entry."""
        # Use a longer timeout for uploads
        timeout = aiohttp.ClientTimeout(total=3600, connect=30, sock_read=300)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session on context exit."""
        if self.session:
            await self.session.close()

    async def upload_file_stream(
        self,
        file_path: Path,
        presigned_url: str,
        max_retries: Optional[int] = None,
        ftp_username: Optional[str] = None,
    ) -> bool:
        """
        Upload a file to S3 using presigned URL with streaming.

        Args:
            file_path: Path to the file to upload
            presigned_url: Presigned URL for upload
            max_retries: Maximum retry attempts (uses Config.MAX_RETRIES if not provided)
            ftp_username: FTP username (camera name) for permission fixes
        """
        if max_retries is None:
            max_retries = Config.MAX_RETRIES

        file_size = file_path.stat().st_size
        file_name = file_path.name

        logger.info(f"Starting upload: {file_name} ({format_bytes(file_size)})")

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                # Stream file upload
                async with aiofiles.open(file_path, "rb") as f:
                    # Prepare headers to avoid chunked transfer (S3 expects Content-Length)
                    headers = {
                        "Content-Length": str(file_size),
                        "Content-Type": get_mime_type(file_path),
                    }

                    # Read file in chunks and upload; provide Content-Length to prevent 411
                    async with self.session.put(
                        presigned_url,
                        data=self._file_chunk_generator(f, file_size, file_name),
                        headers=headers,
                    ) as response:
                        response.raise_for_status()

                        if attempt > 0:
                            logger.info(
                                f"Upload succeeded on attempt {attempt + 1}: {file_name}"
                            )
                        else:
                            logger.info(f"Upload completed: {file_name}")

                        return True

            except (aiohttp.ClientError, OSError) as e:
                last_exception = e

                # Check specifically for Permission Denied (Errno 13)
                import errno

                is_permission_error = False
                if isinstance(e, PermissionError) or (
                    isinstance(e, OSError) and e.errno == errno.EACCES
                ):
                    is_permission_error = True

                if is_permission_error and ftp_username:
                    logger.warning(
                        f"Permission denied for {file_name}. Triggering nsenter fix on host for camera: {ftp_username}"
                    )
                    try:
                        # nsenter -t 1 -m -u -n -i executes the script in the host's namespaces
                        cmd = [
                            "nsenter",
                            "-t",
                            "1",
                            "-m",
                            "-u",
                            "-n",
                            "-i",
                            "/opt/ftp/permissionSetup.sh",
                            ftp_username,
                        ]
                        logger.info(f"Executing nsenter command: {' '.join(cmd)}")

                        process = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        stdout, stderr = await process.communicate()

                        if process.returncode == 0:
                            logger.info(
                                f"nsenter permission fix successful for {ftp_username}"
                            )
                        else:
                            logger.error(
                                f"nsenter permission fix failed (exit {process.returncode}): {stderr.decode()}"
                            )
                    except Exception as fix_err:
                        logger.error(f"Failed to trigger nsenter fix: {fix_err}")

                if attempt < max_retries:
                    delay = Config.RETRY_INITIAL_DELAY * (
                        Config.RETRY_BACKOFF_MULTIPLIER**attempt
                    )
                    logger.warning(
                        f"Upload failed (attempt {attempt + 1}/{max_retries + 1}): {file_name}. "
                        f"Retrying in {delay:.1f}s... Error: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Upload failed after {max_retries + 1} attempts: {file_name}. Error: {e}"
                    )

        return False

    async def _file_chunk_generator(self, file_handle, total_size: int, file_name: str):
        """
        Generator that yields file chunks for streaming upload.

        Args:
            file_handle: Async file handle
            total_size: Total file size in bytes
            file_name: File name for logging

        Yields:
            File chunks
        """
        bytes_read = 0
        last_progress = 0

        while True:
            chunk = await file_handle.read(self.chunk_size)
            if not chunk:
                break

            bytes_read += len(chunk)

            # Log progress every 10%
            progress = int((bytes_read / total_size) * 100)
            if progress >= last_progress + 10:
                logger.debug(
                    f"Upload progress: {file_name} - {progress}% ({format_bytes(bytes_read)}/{format_bytes(total_size)})"
                )
                last_progress = progress

            yield chunk

    async def upload_files_parallel(
        self,
        file_uploads: list[tuple[Path, str, str]],
        max_concurrent: Optional[int] = None,
    ) -> dict[str, bool]:
        """
        Upload multiple files in parallel with concurrency control.

        Args:
            file_uploads: List of (file_path, presigned_url, ftp_username) tuples
            max_concurrent: Maximum concurrent uploads (uses Config.MAX_CONCURRENT_UPLOADS if not provided)

        Returns:
            Dictionary mapping file path to upload success status
        """
        if max_concurrent is None:
            max_concurrent = Config.MAX_CONCURRENT_UPLOADS

        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}

        async def upload_with_semaphore(
            file_path: Path, presigned_url: str, ftp_username: str
        ):
            async with semaphore:
                success = await self.upload_file_stream(
                    file_path, presigned_url, ftp_username=ftp_username
                )
                results[str(file_path)] = success
                return success

        # Create tasks for all uploads
        tasks = [
            upload_with_semaphore(file_path, presigned_url, ftp_username)
            for file_path, presigned_url, ftp_username in file_uploads
        ]

        # Wait for all uploads to complete
        upload_results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions from tasks
        for i, result in enumerate(upload_results_list):
            if isinstance(result, Exception):
                file_path = file_uploads[i][0]
                logger.error(
                    f"Upload task failed with exception: {file_path} - {result}"
                )
                results[str(file_path)] = False

        # Log summary
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful

        logger.info(
            f"Parallel upload completed: {successful} successful, {failed} failed out of {len(results)} total"
        )

        return results
