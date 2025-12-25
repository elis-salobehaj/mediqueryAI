import sys
from unittest.mock import MagicMock

# MOCK HEAVY DEPENDENCIES
# This must run before any application code is imported

# 1. Mock Schema objects often imported at top level
class MockNode:
    def __init__(self, text="", table_name=""):
        self.text = text
        self.table_name = table_name

class MockSQLDatabase:
    def __init__(self, engine, include_tables=None):
        pass

# 2. Define the Mock Modules
mock_llama_index = MagicMock()
mock_llama_index.core = MagicMock()
mock_llama_index.core.SQLDatabase = MockSQLDatabase
mock_llama_index.core.schema.TextNode = MockNode
mock_llama_index.llms = MagicMock()
mock_llama_index.embeddings = MagicMock()

# 3. Patch sys.modules
# We need to cover all namespaces used in the code
sys.modules["llama_index"] = mock_llama_index
sys.modules["llama_index.core"] = mock_llama_index.core
sys.modules["llama_index.core.indices"] = MagicMock()
sys.modules["llama_index.core.indices.struct_store"] = MagicMock()
sys.modules["llama_index.llms.ollama"] = MagicMock()
sys.modules["llama_index.embeddings.huggingface"] = MagicMock()

# Also mock specific classes if they are imported directly 'from x import Y'
# Check llm_agent.py imports to be sure, but usually patching the parent module is enough 
# IF the code does checks like `if sql_retriever:`

import pytest
from fastapi.testclient import TestClient
# We can now safely import app code without triggering ImportError
from main import app

@pytest.fixture
def client():
    return TestClient(app)
