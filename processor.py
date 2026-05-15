"""
Batch processor for file uploads.
Orchestrates validation, upload, commit, and metadata save operations.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from api_client import APIClient
from config import Config
from logger import get_logger
from storage_client import StorageClient
from utils import (
    format_bytes,
    generate_file_id,
    generate_file_key,
    get_file_size,
    get_mime_type,
    parse_ftp_path,
    safe_delete_file,
)

logger = get_logger(__name__)


class BatchProcessor:
    """Processes batches of uploaded files."""

    def __init__(self):
        self.ftp_root = Config.FTP_ROOT_DIR
        # Limit concurrent batch processing to prevent resource exhaustion
        self.processing_semaphore = asyncio.Semaphore(3)  # Max 3 concurrent batches

    async def process_batch(self, files: List[Path]) -> None:
        """
        Process a batch of files.

        Args:
            files: List of file paths to process
        """
        if not files:
            logger.warning("Empty batch received, skipping")
            return

        # Use semaphore to limit concurrent batch processing
        async with self.processing_semaphore:
            logger.info(f"Processing batch of {len(files)} files")

            await self._process_batch_internal(files)

    async def _process_batch_internal(self, files: List[Path]) -> None:
        """
        Internal method to process a batch of files.

        Args:
            files: List of file paths to process
        """
        try:
            # Step 1: Parse file information
            file_info_list = self._parse_files(files)
            if not file_info_list:
                logger.error("No valid files in batch, aborting")
                return

            # Extract user_id (should be same for all files in batch)
            user_id = file_info_list[0]["user_id"]

            # Step 2: Calculate total size and prepare file keys
            total_size = sum(info["file_size"] for info in file_info_list)
            file_keys = [info["file_key"] for info in file_info_list]

            logger.info(
                f"Batch summary: {len(file_info_list)} files, total size: {format_bytes(total_size)}"
            )

            async with APIClient() as api_client, StorageClient() as storage_client:
                # Step 3: Validate storage
                try:
                    reservation_id = await api_client.validate_storage(
                        user_id=user_id, total_file_size=total_size, file_keys=file_keys
                    )
                    logger.info(f"✅ Reservation ID stored safely: {reservation_id}")
                except Exception as e:
                    logger.error(f"Storage validation failed: {e}")
                    return

                # Step 4: Get presigned URLs
                # Prepare files info with fileName and contentType
                files_info = [
                    {"fileName": info["file_key"], "contentType": info["mime_type"]}
                    for info in file_info_list
                ]
                logger.debug(f"Prepared files_info for presigned URLs: {files_info}")
                try:
                    presigned_urls = await api_client.get_presigned_urls(files_info)
                except Exception as e:
                    logger.error(f"Failed to get presigned URLs: {e}")
                    logger.error(f"Files info that was sent: {files_info}")
                    return

                # Step 5: Upload files to S3
                upload_pairs = []
                for info in file_info_list:
                    file_key = info["file_key"]
                    if file_key in presigned_urls:
                        upload_pairs.append(
                            (
                                info["file_path"],
                                presigned_urls[file_key],
                                info["ftp_username"],
                            )
                        )
                    else:
                        logger.warning(f"No presigned URL for file: {file_key}")

                upload_results = await storage_client.upload_files_parallel(
                    upload_pairs
                )

                # Track successful uploads
                successful_files = []
                failed_files = []

                for info in file_info_list:
                    file_path_str = str(info["file_path"])
                    if upload_results.get(file_path_str, False):
                        successful_files.append(info)
                    else:
                        failed_files.append(info)

                if not successful_files:
                    logger.error("All uploads failed, aborting batch")
                    return

                logger.info(
                    f"Upload results: {len(successful_files)} successful, {len(failed_files)} failed"
                )

                # Step 6: Commit storage reservation
                try:
                    logger.info(f"Using stored reservation ID: {reservation_id}")
                    await api_client.commit_storage(reservation_id)
                    logger.info(
                        f"✅ Successfully committed reservation: {reservation_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to commit storage for reservation {reservation_id}: {e}"
                    )
                    # Continue to save metadata even if commit fails

                # Step 7: Save metadata
                metadata_list = self._prepare_metadata(successful_files, presigned_urls)

                try:
                    await api_client.save_metadata(metadata_list)
                except Exception as e:
                    logger.error(f"Failed to save metadata: {e}")
                    # Continue to cleanup even if metadata save fails

                # Step 8: Cleanup successfully uploaded files
                for info in successful_files:
                    safe_delete_file(info["file_path"])

                logger.info(
                    f"Batch processing completed: {len(successful_files)} files uploaded and cleaned up"
                )

        except Exception as e:
            logger.error(f"Unexpected error processing batch: {e}", exc_info=True)

    def _parse_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """
        Parse file information from paths.

        Args:
            files: List of file paths

        Returns:
            List of file information dictionaries
        """
        file_info_list = []

        for file_path in files:
            # Parse FTP path
            path_info = parse_ftp_path(file_path, self.ftp_root)
            if not path_info:
                logger.warning(f"Skipping file with invalid path: {file_path}")
                continue

            username_userid, user_id, ftp_username = path_info

            # Get file information
            file_name = file_path.name
            file_size = get_file_size(file_path)
            mime_type = get_mime_type(file_path)
            file_id = generate_file_id()
            file_key = generate_file_key(username_userid, ftp_username, file_name)

            file_info_list.append(
                {
                    "file_path": file_path,
                    "file_id": file_id,
                    "file_name": file_name,
                    "file_size": file_size,
                    "mime_type": mime_type,
                    "file_key": file_key,
                    "user_id": user_id,
                    "username_userid": username_userid,
                    "ftp_username": ftp_username,
                }
            )

        return file_info_list

    def _prepare_metadata(
        self, file_info_list: List[Dict[str, Any]], presigned_urls: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Prepare metadata for bulk save.

        Args:
            file_info_list: List of file information dictionaries
            presigned_urls: Dictionary of presigned URLs

        Returns:
            List of metadata dictionaries
        """
        metadata_list = []

        for info in file_info_list:
            file_key = info["file_key"]

            # Extract base URL from presigned URL (remove query parameters)
            presigned_url = presigned_urls.get(file_key, "")
            s3_url = presigned_url.split("?")[0] if presigned_url else ""

            # Construct metadata
            metadata = {
                "fileId": info["file_id"],
                "fileName": info["file_name"],
                "mime_type": info["mime_type"],
                "friendlyUrl": s3_url,  # Adjust based on your URL structure
                "downloadUrl": s3_url,
                "nativeUrl": s3_url,
                "s3Url": s3_url,
                "folder": f"{info['username_userid']}/ftp/{info['ftp_username']}",
                "filesize": info["file_size"] / (1024**3),  # Convert to GB
                "folderId": "ftp",  # Set if you have folder IDs
                "userId": info["user_id"],
                # Use the FTP username (last folder segment) as the projectId
                "projectId": info["ftp_username"],
            }

            metadata_list.append(metadata)

        logger.info(
            f"Prepared metadata for bulk save: {json.dumps(metadata_list, indent=2)}"
        )
        return metadata_list
