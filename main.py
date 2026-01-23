"""
Main entry point for FTP upload processor.
"""

import asyncio
import signal
import sys

from config import Config
from logger import get_logger
from processor import BatchProcessor
from watcher import FileWatcher

logger = get_logger(__name__)


class Application:
    """Main application class."""

    def __init__(self):
        self.processor = BatchProcessor()
        self.watcher = FileWatcher(self.processor.process_batch)
        self.running = False
        self.pending_tasks = set()

    async def start(self):
        """Start the application."""
        logger.info("=" * 80)
        logger.info("FTP Upload Processor Starting")
        logger.info("=" * 80)
        logger.info(Config.display())

        # Get event loop
        loop = asyncio.get_event_loop()

        # Start file watcher
        self.watcher.start(loop)
        self.running = True

        logger.info("Application started successfully")
        logger.info("Monitoring FTP directories for new uploads...")

        # Keep running until interrupted
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Application interrupted")
        finally:
            await self._cleanup_tasks()

    async def _cleanup_tasks(self):
        """Cleanup pending async tasks."""
        if self.pending_tasks:
            logger.info(
                f"Waiting for {len(self.pending_tasks)} pending tasks to complete..."
            )
            await asyncio.gather(*self.pending_tasks, return_exceptions=True)
            logger.info("All pending tasks completed")

    def stop(self):
        """Stop the application."""
        logger.info("Stopping application...")
        self.running = False
        self.watcher.stop()
        logger.info("Application stopped")


def signal_handler(app: Application, loop: asyncio.AbstractEventLoop):
    """Handle shutdown signals."""

    def handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        app.stop()
        # Cancel all running tasks
        for task in asyncio.all_tasks(loop):
            task.cancel()

    return handler


async def main():
    """Main entry point."""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    # Create application
    app = Application()

    # Get event loop
    loop = asyncio.get_event_loop()

    # Register signal handlers
    handler = signal_handler(app, loop)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    # Start application
    try:
        await app.start()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        app.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
