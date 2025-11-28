"""Pytest configuration and fixtures"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture
def reset_activities(client):
    """Reset activities to initial state after each test"""
    # Store initial state
    response = client.get("/activities")
    initial_activities = response.json()
    
    yield client
    
    # Reset to initial state by re-importing the app module
    # This ensures activities are reset between tests
    import importlib
    import sys
    if 'src.app' in sys.modules:
        importlib.reload(sys.modules['src.app'])
