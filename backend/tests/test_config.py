from fastapi.testclient import TestClient
from unittest.mock import patch
import os
import pytest
from main import app

client = TestClient(app)

def test_get_models_cloud_default():
    """Test /config/models returns cloud models when USE_LOCAL_MODEL is false."""
    with patch.dict(os.environ, {"USE_LOCAL_MODEL": "false", "USE_BEDROCK": "false"}):
        # Re-init agent or mock its state because it loads env vars at init
        with patch("services.llm_agent.llm_agent.use_local", False):
            with patch("services.llm_agent.llm_agent.use_bedrock", False):
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
            # Verify our top picks are present
            assert any(m["id"] == "qwen2.5-coder:7b" for m in models)
            assert any(m["id"] == "sqlcoder:7b" for m in models)
            assert any(m["id"] == "llama3.1" for m in models)

def test_get_models_bedrock():
    """Test /config/models returns Bedrock models when USE_BEDROCK is true."""
    with patch.dict(os.environ, {
        "USE_BEDROCK": "true",
        "USE_LOCAL_MODEL": "false",
        "BEDROCK_SQL_WRITER_MODEL": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "BEDROCK_NAVIGATOR_MODEL": "anthropic.claude-3-5-haiku-20241022-v1:0",
        "BEDROCK_CRITIC_MODEL": "anthropic.claude-3-5-haiku-20241022-v1:0"
    }):
        with patch("services.llm_agent.llm_agent.use_bedrock", True):
            with patch("services.llm_agent.llm_agent.use_local", False):
                response = client.get("/config/models")
                assert response.status_code == 200
                models = response.json()
                assert len(models) == 3
                # Verify Bedrock models are present
                assert any("Sonnet" in m["name"] for m in models)
                assert any("Haiku" in m["name"] for m in models)
