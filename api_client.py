"""
API client for backend interactions.
Handles storage validation, presigned URLs, commits, and metadata uploads.
"""

import asyncio
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientTimeout

from config import Config
from logger import get_logger

logger = get_logger(__name__)


class APIClient:
    """Async HTTP client for backend API interactions."""

    def __init__(self):
        self.base_url = Config.API_BASE_URL.rstrip("/")
        self.uploads_base_url = Config.API_UPLOADS_BASE_URL.rstrip("/")
        self.auth_token = Config.API_AUTH_TOKEN
        self.timeout = ClientTimeout(total=Config.API_TIMEOUT)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Create aiohttp session on context entry."""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "*/*",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session on context exit."""
        if self.session:
            await self.session.close()

    async def _retry_request(
        self, method: str, url: str, require_auth: bool = True, **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            require_auth: Whether to include Authorization header
            **kwargs: Additional arguments for aiohttp request

        Returns:
            Response JSON data

        Raises:
            Exception if all retries fail
        """
        last_exception = None

        # Add Authorization header if required
        if require_auth:
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            kwargs["headers"]["Authorization"] = f"Bearer {self.auth_token}"

        for attempt in range(Config.MAX_RETRIES + 1):
            try:
                # Log the outgoing request details
                if attempt == 0:
                    logger.info(f"Making {method} request to: {url}")
                    logger.debug(f"Request kwargs: {kwargs}")

                async with self.session.request(method, url, **kwargs) as response:
                    # Log response details
                    logger.info(f"Response status: {response.status}")
                    logger.debug(f"Response headers: {response.headers}")

                    response.raise_for_status()

                    # Get response text first for debugging
                    response_text = await response.text()
                    logger.debug(f"Response text: {response_text[:500]}")

                    # Try to parse as JSON
                    try:
                        import json

                        data = json.loads(response_text)
                    except json.JSONDecodeError as json_err:
                        logger.error(f"Failed to parse JSON response: {json_err}")
                        logger.error(f"Response text: {response_text}")
                        raise ValueError(
                            f"Invalid JSON response: {json_err}. Response: {response_text[:200]}"
                        )

                    if attempt > 0:
                        logger.info(
                            f"Request succeeded on attempt {attempt + 1}: {method} {url}"
                        )

                    return data

            except aiohttp.ClientError as e:
                last_exception = e

                if attempt < Config.MAX_RETRIES:
                    delay = Config.RETRY_INITIAL_DELAY * (
                        Config.RETRY_BACKOFF_MULTIPLIER**attempt
                    )
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{Config.MAX_RETRIES + 1}): {method} {url}. "
                        f"Retrying in {delay:.1f}s... Error: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Request failed after {Config.MAX_RETRIES + 1} attempts: {method} {url}. Error: {e}"
                    )

        raise last_exception

    async def validate_storage(
        self, user_id: str, total_file_size: int, file_keys: List[str]
    ) -> str:
        """
        Validate storage availability and create reservation.

        Args:
            user_id: User ID
            total_file_size: Total size of all files in bytes
            file_keys: List of S3 object keys

        Returns:
            Reservation ID
        """
        # Convert bytes to GB and format to reasonable precision
        total_file_size_gb = total_file_size / (1024**3)
        # Round to 6 decimal places to avoid floating point precision issues
        total_file_size_gb = round(total_file_size_gb, 6)

        url = f"{self.base_url}/storage/validate/{user_id}/{total_file_size_gb}"
        payload = {"fileKeys": file_keys}

        logger.info(
            f"Validating storage for user {user_id}: {total_file_size} bytes ({total_file_size_gb:.6f} GB), {len(file_keys)} files"
        )

        response = await self._retry_request("POST", url, json=payload)

        reservation_id = response.get("reservationId")
        if not reservation_id:
            raise ValueError(f"No reservationId in response: {response}")

        logger.info(f"Storage validated successfully. Reservation ID: {reservation_id}")
        return reservation_id

    async def get_presigned_urls(
        self, files_info: List[Dict[str, str]]
    ) -> Dict[str, str]:
        """
        Get presigned URLs for file uploads.

        Args:
            files_info: List of dicts with 'fileName' and 'contentType' keys

        Returns:
            Dictionary mapping fileName to presigned_url
        """
        url = f"{self.uploads_base_url}/uploads/presigned-urls"
        payload = {"files": files_info}

        logger.info(f"Requesting presigned URLs for {len(files_info)} files")
        logger.debug(f"Presigned URLs request payload: {payload}")

        try:
            response = await self._retry_request("POST", url, json=payload)
        except Exception as e:
            logger.error(f"Failed to get response from presigned URLs API: {e}")
            raise

        logger.info(f"Raw response type: {type(response)}")
        logger.info(f"Raw response content: {response}")

        # Handle different response formats
        try:
            if isinstance(response, str):
                # Response is a string - this is unexpected, log and raise error
                logger.error(f"API returned string instead of JSON: {response[:200]}")
                raise ValueError(
                    f"Presigned URLs API returned a string instead of JSON. "
                    f"This usually means an error page or unexpected response. "
                    f"Response preview: {response[:200]}"
                )
            elif isinstance(response, list):
                logger.info(f"Response is a list with {len(response)} items")

                # Check if list contains strings (URLs) or objects
                if response and isinstance(response[0], str):
                    # Response is a list of URL strings in the same order as request
                    logger.info("Response is a list of URL strings")
                    if len(response) != len(files_info):
                        raise ValueError(
                            f"Response length ({len(response)}) doesn't match request length ({len(files_info)})"
                        )
                    # Map fileName to URL based on order
                    presigned_urls = {
                        files_info[i]["fileName"]: response[i]
                        for i in range(len(response))
                    }
                else:
                    # Response is a list of objects with fileName and url
                    logger.info("Response is a list of objects")
                    presigned_urls = {}
                    for item in response:
                        logger.debug(f"Processing item: {item}")
                        presigned_urls[item["fileName"]] = item["url"]
            elif isinstance(response, dict):
                # Response might have 'urls' key or be flat dict
                logger.info("Response is a dict")
                presigned_urls = response.get("urls", response)
            else:
                raise ValueError(
                    f"Unexpected response format for presigned URLs: {type(response)}, value: {response}"
                )
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Error parsing response: {e}")
            logger.error(f"Response structure: {response}")
            raise ValueError(
                f"Failed to parse presigned URLs response: {e}. Response: {response}"
            )

        if not isinstance(presigned_urls, dict):
            raise ValueError(
                f"Expected dict of presigned URLs, got: {type(presigned_urls)}"
            )

        logger.info(f"Received {len(presigned_urls)} presigned URLs")
        logger.debug(f"Presigned URLs mapping: {presigned_urls}")
        return presigned_urls

    async def commit_storage(self, reservation_id: str) -> Dict[str, Any]:
        """
        Commit storage reservation after successful uploads.

        Args:
            reservation_id: Reservation ID from validate_storage

        Returns:
            Response data
        """
        url = f"{self.base_url}/storage/commit/{reservation_id}"

        logger.info(f"Committing storage reservation: {reservation_id}")

        response = await self._retry_request("POST", url)

        logger.info(f"Storage committed successfully: {reservation_id}")
        return response

    async def save_metadata(
        self, files_metadata: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Save file metadata in bulk.

        Args:
            files_metadata: List of file metadata dictionaries

        Returns:
            Response data
        """
        if not files_metadata:
            raise ValueError("files_metadata cannot be empty")

        # Extract userId from the first file metadata (all files should have the same userId)
        user_id = files_metadata[0].get("userId")
        if not user_id:
            raise ValueError("userId is required in file metadata")

        url = f"{self.uploads_base_url}/uploads/ftp/bulk/{user_id}"
        payload = {"files": files_metadata}

        logger.info(
            f"Saving metadata for {len(files_metadata)} files for user {user_id}"
        )
        logger.info(f"API Request URL: {url}")
        logger.info(f"API Request Method: POST")
        logger.info(f"API Request Payload: {payload}")

        response = await self._retry_request(
            "POST", url, require_auth=False, json=payload
        )

        logger.info(f"Metadata saved successfully for {len(files_metadata)} files")
        logger.info(f"API Response: {response}")
        return response
