"""
Unit tests for configuration.
"""

import pytest
import os
from config import Config


def test_config_defaults():
    """Test configuration defaults."""
    assert Config.BATCH_SIZE == 10
    assert Config.MAX_CONCURRENT_UPLOADS == 4
    assert Config.MAX_RETRIES == 3
    assert Config.UPLOAD_CHUNK_SIZE == 1048576  # 1MB


def test_config_display():
    """Test configuration display."""
    display = Config.display()
    assert "API Base URL" in display
    assert "Batch Size" in display
    assert "Max Concurrent Uploads" in display
