from unittest.mock import patch, MagicMock
import os
import sys
from config import settings

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_agent import LLMAgent

def test_semantic_setup_flow():
    """Test that the semantic engine setup logic runs if dependencies are present."""
    with patch('services.llm_agent.HAS_LLAMA_INDEX', True):
        # Mock all LlamaIndex components that are imported/used
        with patch('services.llm_agent.SQLDatabase', create=True) as MockDB, \
             patch('services.llm_agent.create_engine', create=True) as MockEngine, \
             patch('services.llm_agent.SQLTableNodeMapping', create=True), \
             patch('services.llm_agent.SQLTableSchema', create=True), \
             patch('services.llm_agent.Settings', create=True), \
             patch('services.llm_agent.HuggingFaceEmbedding', create=True), \
             patch('services.llm_agent.VectorStoreIndex', create=True), \
             patch('services.llm_agent.ObjectIndex', create=True) as MockIndex:
             
            # Setup mocks
            MockDB.return_value.get_usable_table_names.return_value = ["patients", "visits"]
            MockIndex.from_objects.return_value.as_retriever.return_value = MagicMock()

            # Init agent
            agent = LLMAgent()
            agent.settings = settings # Provide settings
            agent._setup_semantic_engine()
            
            # Assertions
            assert MockIndex.from_objects.called
            assert agent.sql_retriever is not None
            
            # Verify log thought
            assert "Initializing Semantic Engine..." in agent.last_thoughts

def test_semantic_retrieval_flow():
    """Test that generate_sql uses retrieval if available."""
    with patch('services.llm_agent.HAS_LLAMA_INDEX', True):
        agent = LLMAgent()
        agent.settings = settings
        agent.settings.use_local_model = True
        
        # Manually attach a mock retriever
        mock_retriever = MagicMock()
        mock_node = MagicMock()
        mock_node.table_name = "patients"
        mock_retriever.retrieve.return_value = [mock_node]
        agent.sql_retriever = mock_retriever
        
        # Mock _call_ollama to avoid actual call
        agent._call_ollama = MagicMock(return_value="SELECT * FROM patients")
        agent.model = None # Use local/default logic
        
        agent.generate_sql("list patients", "SCHEMA", [])
        
        # Verify retrieval called
        mock_retriever.retrieve.assert_called_with("list patients")
        
        # Verify thoughts captured
        assert "Using Semantic Search to identify relevant tables..." in agent.last_thoughts
        assert "Identified tables: patients" in agent.last_thoughts
