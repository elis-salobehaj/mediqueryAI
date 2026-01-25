import os
import pytest
from config import Settings

def test_settings_load_from_env():
    # Set dummy env vars for testing
    os.environ["GEMINI_API_KEY"] = "test_key"
    os.environ["USE_BEDROCK"] = "true"
    
    settings = Settings()
    assert settings.gemini_api_key == "test_key"
    assert settings.use_bedrock == True
    
    # Cleanup
    del os.environ["GEMINI_API_KEY"]
    del os.environ["USE_BEDROCK"]

def test_settings_defaults():
    settings = Settings()
    assert settings.log_level == "DEBUG"
    assert settings.aws_bedrock_region == "us-west-2"
