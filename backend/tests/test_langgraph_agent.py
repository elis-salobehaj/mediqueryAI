"""
Unit tests for LangGraph Multi-Agent SQL Generation Workflow

Tests each agent node and the overall workflow coordination.
"""

import pytest
import asyncio
from services.langgraph_agent import MultiAgentSQLGenerator, AgentState
from services.database import db_service
from services.llm_agent import llm_agent


class TestMultiAgentWorkflow:
    """Test suite for multi-agent SQL generation."""
    
    @pytest.fixture
    def multi_agent(self):
        """Create MultiAgentSQLGenerator instance."""
        return MultiAgentSQLGenerator(
            database_service=db_service,
            llm_agent=llm_agent,
            config={
                "timeout_seconds": 30,
                "max_attempts": 2,
            }
        )
    
    def test_multi_agent_initialization(self, multi_agent):
        """Test that MultiAgentSQLGenerator initializes correctly."""
        assert multi_agent is not None
        assert multi_agent.db_service == db_service
        assert multi_agent.llm_agent == llm_agent
        assert multi_agent.config["timeout_seconds"] == 30
        assert multi_agent.config["max_attempts"] == 2
    
    def test_agent_state_structure(self):
        """Test AgentState TypedDict structure."""
        state: AgentState = {
            "messages": [],
            "original_query": "Test query",
            "username": "test_user",
            "query_plan": None,
            "selected_tables": [],
            "table_schemas": {},
            "generated_sql": None,
            "validation_result": None,
            "reflections": [],
            "attempt_count": 0,
            "max_attempts": 3,
            "timeout_seconds": 60.0,
            "start_time": 0.0,
            "thoughts": [],
            "agent_mode": "multi-agent",
        }
        
        assert state["original_query"] == "Test query"
        assert state["max_attempts"] == 3
        assert state["agent_mode"] == "multi-agent"
    
    @pytest.mark.asyncio
    async def test_simple_query_execution(self, multi_agent):
        """Test full workflow with a simple query."""
        # Skip if no API keys configured
        import os
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not configured")
        
        result = await multi_agent.ainvoke(
            query="How many patients do we have?",
            username="test_user"
        )
        
        assert result is not None
        assert "agent_mode" in result
        assert result["agent_mode"] == "multi-agent"
        assert "sql" in result
        assert "thoughts" in result
        assert isinstance(result["thoughts"], list)
    
    @pytest.mark.asyncio
    async def test_schema_navigator_selects_tables(self, multi_agent):
        """Test that Schema Navigator correctly identifies relevant tables."""
        from langchain_core.messages import HumanMessage
        
        initial_state: AgentState = {
            "messages": [HumanMessage(content="Show patient demographics")],
            "original_query": "Show patient demographics",
            "username": "test_user",
            "query_plan": None,
            "selected_tables": [],
            "table_schemas": {},
            "generated_sql": None,
            "validation_result": None,
            "reflections": [],
            "attempt_count": 0,
            "max_attempts": 3,
            "timeout_seconds": 60.0,
            "start_time": 0.0,
            "thoughts": [],
            "agent_mode": "multi-agent",
        }
        
        result_state = multi_agent._schema_navigator_node(initial_state)
        
        assert "selected_tables" in result_state
        assert len(result_state["selected_tables"]) > 0
        assert "patients" in result_state["selected_tables"]  # Should select patients table
    
    def test_should_continue_logic(self, multi_agent):
        """Test conditional routing logic."""
        import time
        
        # Test timeout
        timeout_state: AgentState = {
            "messages": [],
            "original_query": "",
            "username": None,
            "query_plan": None,
            "selected_tables": [],
            "table_schemas": {},
            "generated_sql": None,
            "validation_result": None,
            "reflections": [],
            "attempt_count": 1,
            "max_attempts": 3,
            "timeout_seconds": 1.0,
            "start_time": time.time() - 2.0,  # 2 seconds ago
            "thoughts": [],
            "agent_mode": "multi-agent",
        }
        
        assert multi_agent._should_continue(timeout_state) == "timeout"
        
        # Test max attempts
        max_attempts_state: AgentState = {
            "messages": [],
            "original_query": "",
            "username": None,
            "query_plan": None,
            "selected_tables": [],
            "table_schemas": {},
            "generated_sql": None,
            "validation_result": None,
            "reflections": [],
            "attempt_count": 3,
            "max_attempts": 3,
            "timeout_seconds": 60.0,
            "start_time": time.time(),
            "thoughts": [],
            "agent_mode": "multi-agent",
        }
        
        assert multi_agent._should_continue(max_attempts_state) == "max_attempts"
        
        # Test success
        success_state: AgentState = {
            "messages": [],
            "original_query": "",
            "username": None,
            "query_plan": None,
            "selected_tables": [],
            "table_schemas": {},
            "generated_sql": "SELECT * FROM patients",
            "validation_result": {"valid": True, "row_count": 10},
            "reflections": [],
            "attempt_count": 1,
            "max_attempts": 3,
            "timeout_seconds": 60.0,
            "start_time": time.time(),
            "thoughts": [],
            "agent_mode": "multi-agent",
        }
        
        assert multi_agent._should_continue(success_state) == "success"
    
    def test_config_defaults(self):
        """Test that default configuration values are set correctly."""
        multi_agent = MultiAgentSQLGenerator(
            database_service=db_service,
            llm_agent=llm_agent
        )
        
        assert multi_agent.config["timeout_seconds"] == 120
        assert multi_agent.config["max_attempts"] == 3
        assert "schema_navigator_model" in multi_agent.config
        assert "sql_writer_model" in multi_agent.config
        assert "critic_model" in multi_agent.config
    
    def test_reflect_node_generates_feedback(self, multi_agent):
        """Test that reflect node generates actionable feedback."""
        state: AgentState = {
            "messages": [],
            "original_query": "Show patients",
            "username": None,
            "query_plan": None,
            "selected_tables": [],
            "table_schemas": {},
            "generated_sql": "SELECT * FROM invalid_table",
            "validation_result": {
                "valid": False,
                "error": "no such table: invalid_table",
                "row_count": 0,
                "warnings": []
            },
            "reflections": [],
            "attempt_count": 1,
            "max_attempts": 3,
            "timeout_seconds": 60.0,
            "start_time": 0.0,
            "thoughts": [],
            "agent_mode": "multi-agent",
        }
        
        result_state = multi_agent._reflect_node(state)
        
        assert len(result_state["reflections"]) == 1
        assert "invalid_table" in result_state["reflections"][0]
        assert "Attempt 1 failed" in result_state["reflections"][0]


class TestMultiAgentIntegration:
    """Integration tests for multi-agent workflow."""
    
    @pytest.mark.asyncio
    async def test_fallback_to_single_agent_on_error(self):
        """Test graceful degradation when multi-agent fails."""
        # This would be tested via the API endpoint
        # Simulating a multi-agent failure and checking fallback
        pass
    
    @pytest.mark.asyncio
    async def test_hybrid_routing_toggle(self):
        """Test that multi_agent=True routes to LangGraph workflow."""
        # This would be tested via the API endpoint
        # Check that the response contains agent_mode="multi"
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
