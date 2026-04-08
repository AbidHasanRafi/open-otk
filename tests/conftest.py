"""Shared fixtures for the OTK test suite."""

import os
import sys
import tempfile
import pytest

# Ensure the package root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mock_ollama import MockOllamaClient


@pytest.fixture
def mock_client():
    """Return a fresh MockOllamaClient."""
    return MockOllamaClient()


@pytest.fixture
def tmp_dir(tmp_path):
    """Return a temporary directory path (pathlib.Path)."""
    return tmp_path


@pytest.fixture
def tmp_db(tmp_path):
    """Return a path to a temporary SQLite database file."""
    return str(tmp_path / "test.db")
