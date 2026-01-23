"""
File watcher for FTP upload directories.
Uses inotify for event-driven file detection with batching.
"""

import asyncio
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List

from watchdog.events import FileClosedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from config import Config
from logger import get_logger
from utils import parse_ftp_path

logger = get_logger(__name__)


class FileUploadHandler(FileSystemEventHandler):
    """Handler for file upload events."""

    def __init__(self, callback: Callable, ftp_root: Path):
        """
        Initialize file upload handler.

        Args:
            callback: Async callback function to process file batches
            ftp_root: FTP root directory
        """
        super().__init__()
        self.callback = callback
        self.ftp_root = ftp_root
        self.file_batches: Dict[str, List[Path]] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}
        self.loop = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the event loop for async operations."""
        self.loop = loop

    def on_closed(self, event):
        """
        Handle file close event (upload complete).

        Args:
            event: FileClosedEvent from watchdog
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Parse FTP path to get user info
        path_info = parse_ftp_path(file_path, self.ftp_root)
        if not path_info:
            logger.warning(f"Ignoring file with invalid path: {file_path}")
            return

        username_userid, user_id, ftp_username = path_info

        # Use user_id and ftp_username as batch key to separate jobs by folder
        batch_key = f"{user_id}_{ftp_username}"

        logger.info(
            f"File upload detected: {file_path.name} (user: {username_userid}, batch: {batch_key})"
        )

        # Add file to batch
        self.file_batches[batch_key].append(file_path)

        # Check if batch is full
        if len(self.file_batches[batch_key]) >= Config.BATCH_SIZE:
            logger.info(
                f"Batch full ({Config.BATCH_SIZE} files) for user {batch_key}, triggering processing"
            )
            self._trigger_batch_processing(batch_key)
        else:
            # Start or reset batch timer
            self._reset_batch_timer(batch_key)

    def _reset_batch_timer(self, batch_key: str):
        """
        Reset the batch timer for a user.

        Args:
            batch_key: User ID for batch grouping
        """
        # Cancel existing timer if any
        if batch_key in self.batch_timers:
            self.batch_timers[batch_key].cancel()
            del self.batch_timers[batch_key]  # Clean up cancelled task

        # Create new timer
        if self.loop:
            self.batch_timers[batch_key] = self.loop.create_task(
                self._batch_timeout(batch_key)
            )

    async def _batch_timeout(self, batch_key: str):
        """
        Handle batch timeout - process incomplete batch.

        Args:
            batch_key: User ID for batch grouping
        """
        try:
            await asyncio.sleep(Config.BATCH_TIMEOUT_SECONDS)

            if batch_key in self.file_batches and self.file_batches[batch_key]:
                logger.info(
                    f"Batch timeout reached for user {batch_key} "
                    f"({len(self.file_batches[batch_key])} files), triggering processing"
                )
                self._trigger_batch_processing(batch_key)

        except asyncio.CancelledError:
            # Timer was cancelled, ignore
            pass

    def _trigger_batch_processing(self, batch_key: str):
        """
        Trigger batch processing for a user.

        Args:
            batch_key: User ID for batch grouping
        """
        # Cancel and remove timer if exists
        if batch_key in self.batch_timers:
            self.batch_timers[batch_key].cancel()
            del self.batch_timers[batch_key]  # Clean up cancelled task

        # Get batch files
        batch_files = self.file_batches.pop(batch_key, [])

        if not batch_files:
            return

        # Schedule callback in event loop
        if self.loop:
            self.loop.create_task(self.callback(batch_files))


class FileWatcher:
    """File watcher for FTP upload directories."""

    def __init__(self, callback: Callable):
        """
        Initialize file watcher.

        Args:
            callback: Async callback function to process file batches
        """
        self.ftp_root = Config.FTP_ROOT_DIR
        self.callback = callback
        self.observer = Observer()
        self.handler = FileUploadHandler(callback, self.ftp_root)
        self.running = False

    def start(self, loop: asyncio.AbstractEventLoop):
        """
        Start watching FTP directories.

        Args:
            loop: Event loop for async operations
        """
        if not self.ftp_root.exists():
            raise ValueError(f"FTP root directory does not exist: {self.ftp_root}")

        # Set event loop for handler
        self.handler.set_event_loop(loop)

        # Schedule observer to watch FTP root recursively
        self.observer.schedule(self.handler, str(self.ftp_root), recursive=True)

        # Start observer
        self.observer.start()
        self.running = True

        logger.info(f"File watcher started, monitoring: {self.ftp_root}")

    def stop(self):
        """Stop watching FTP directories."""
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            logger.info("File watcher stopped")
