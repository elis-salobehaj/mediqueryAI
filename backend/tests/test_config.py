from fastapi.testclient import TestClient
from unittest.mock import patch
import os
import pytest
from main import app

client = TestClient(app)

def test_get_models_cloud_default():
    """Test /config/models returns cloud models when USE_LOCAL_MODEL is false."""
    with patch.dict(os.environ, {"USE_LOCAL_MODEL": "false"}):
        # Re-init agent or mock its state because it loads env vars at init
        with patch("services.llm_agent.llm_agent.use_local", False):
            response = client.get("/config/models")
            assert response.status_code == 200
            models = response.json()
            assert len(models) == 3
            assert models[0]["id"] == "gemma-3-27b-it"

def test_get_models_local():
    """Test /config/models returns local models when USE_LOCAL_MODEL is true."""
    with patch.dict(os.environ, {"USE_LOCAL_MODEL": "true"}):
        with patch("services.llm_agent.llm_agent.use_local", True):
            response = client.get("/config/models")
            assert response.status_code == 200
            models = response.json()
            assert len(models) >= 3
            assert models[0]["id"] == "qwen3:latest"
            assert any(m["id"] == "gemma3:4b" for m in models)
