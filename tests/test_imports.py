"""Test basic imports and module structure."""

import pytest


def test_import_bring_api():
    """Test that BringAPI can be imported."""
    from bring_mcp.bring_api import BringAPI, BringAPIError

    assert BringAPI is not None
    assert BringAPIError is not None


def test_import_server():
    """Test that server module can be imported."""
    from bring_mcp import server

    assert server is not None
    assert hasattr(server, "app")
    assert hasattr(server, "main")


def test_version():
    """Test that package version is defined."""
    import bring_mcp

    assert hasattr(bring_mcp, "__version__")
    assert bring_mcp.__version__ == "0.1.0"
