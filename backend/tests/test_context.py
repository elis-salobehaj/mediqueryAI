import pytest
from services.llm_agent import llm_agent
from config import settings
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_genai():
    with patch('services.llm_agent.HAS_GOOGLE_GENAI', True), \
         patch('services.llm_agent.genai', create=True) as mock_g:
        yield mock_g

def test_llm_agent_history_integration(mock_genai, monkeypatch):
    # Mock settings
    monkeypatch.setattr(settings, "use_local_model", False)
    monkeypatch.setattr(settings, "use_bedrock", False)
    monkeypatch.setattr(settings, "gemini_api_key", "test_key")
    
    class MockResponse:
        def __init__(self):
            self.text = "SELECT * FROM patients WHERE name LIKE '%John%'"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MockResponse()
    
    llm_agent.client = mock_client
    llm_agent.settings = settings
    llm_agent.api_key = "test_key"
    
    history = [
        {"role": "user", "text": "Who is sick?"},
        {"role": "bot", "text": "John Doe is sick."}
    ]
    
    sql = llm_agent.generate_sql("Details about him", "Table: patients", history=history)
    assert sql == "SELECT * FROM patients WHERE name LIKE '%John%'"
