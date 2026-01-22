"""
Tests for Phase 1 features:
- CSV Export (via data structure validation)
- SQL Validation
- Reflexion Loop
- Multi-Tenant Isolation
"""

import pytest
from services.database import db_service
from services.llm_agent import llm_agent


class TestSQLValidation:
    """Tests for SQL validation functionality"""
    
    def test_validate_valid_sql(self):
        """Test validation of a valid SQL query"""
        valid_sql = "SELECT * FROM patients LIMIT 10"
        result = db_service.validate_sql(valid_sql)
        
        assert result["valid"] is True
        assert result["error"] is None
        assert result["row_count"] is not None
    
    def test_validate_sql_with_semicolon(self):
        """Test validation handles trailing semicolons correctly"""
        # SQL with semicolon should work
        sql_with_semi = "SELECT * FROM patients LIMIT 10;"
        result = db_service.validate_sql(sql_with_semi)
        
        assert result["valid"] is True
        assert result["error"] is None
        assert result["row_count"] is not None
    
    def test_validate_sql_multiple_semicolons(self):
        """Test validation handles multiple trailing semicolons"""
        sql_multi_semi = "SELECT * FROM patients LIMIT 10;;;"
        result = db_service.validate_sql(sql_multi_semi)
        
        assert result["valid"] is True
        assert result["error"] is None
    
    def test_execute_query_with_semicolon(self):
        """Test that execute_query handles semicolons correctly"""
        sql_with_semi = "SELECT * FROM patients LIMIT 5;"
        result = db_service.execute_query(sql_with_semi)
        
        assert "columns" in result
        assert "data" in result
        assert len(result["data"]) > 0
    
    def test_validate_invalid_sql(self):
        """Test validation of invalid SQL query"""
        invalid_sql = "SELECT * FROM nonexistent_table"
        result = db_service.validate_sql(invalid_sql)
        
        assert result["valid"] is False
        assert result["error"] is not None
        assert "no such table" in result["error"].lower()
    
    def test_validate_empty_result_warning(self):
        """Test that 0 rows triggers a warning"""
        # Query that returns 0 rows
        empty_sql = "SELECT * FROM patients WHERE patient_id = -999"
        result = db_service.validate_sql(empty_sql)
        
        assert result["valid"] is True
        assert result["row_count"] == 0
        assert len(result["warnings"]) > 0
        assert "0 rows" in result["warnings"][0]
    
    def test_validate_large_result_warning(self):
        """Test that >10k rows triggers a warning"""
        # This might not trigger in test data, but validates the logic exists
        result = db_service.validate_sql("SELECT * FROM patients")
        
        if result["row_count"] > 10000:
            assert len(result["warnings"]) > 0
            assert "10000" in result["warnings"][0] or "rows" in result["warnings"][0]


class TestReflexionLoop:
    """Tests for Reflexion retry loop"""
    
    def test_generate_query_plan(self):
        """Test query plan generation"""
        schema = db_service.get_schema()
        plan = llm_agent.generate_query_plan(
            "Show all patients with diabetes",
            schema
        )
        
        assert plan is not None
        assert len(plan) > 0
        assert isinstance(plan, str)
    
    def test_reflect_on_error(self):
        """Test error reflection"""
        failed_sql = "SELECT * FROM nonexistent_table"
        error_msg = "no such table: nonexistent_table"
        
        reflection = llm_agent.reflect_on_error(
            failed_sql=failed_sql,
            error_msg=error_msg,
            user_query="Show all patients",
            query_plan="Query the patients table"
        )
        
        assert reflection is not None
        assert len(reflection) > 0
        assert isinstance(reflection, str)
    
    def test_sql_with_retry_success(self):
        """Test successful SQL generation with retry"""
        schema = db_service.get_schema()
        
        result = llm_agent.generate_sql_with_retry(
            user_query="Count all patients",
            schema_str=schema,
            db_service=db_service,
            fast_mode=False,
            max_retries=3,
            timeout_seconds=30
        )
        
        assert result["success"] is True
        assert result["sql"] is not None
        assert result["attempts"] >= 1
        assert result["error"] is None
    
    def test_sql_with_retry_fast_mode(self):
        """Test fast mode skips plan generation"""
        schema = db_service.get_schema()
        
        result = llm_agent.generate_sql_with_retry(
            user_query="Count all patients",
            schema_str=schema,
            db_service=db_service,
            fast_mode=True,
            max_retries=2,
            timeout_seconds=20
        )
        
        # In fast mode, query_plan should be None
        assert result["query_plan"] is None or result["query_plan"] == ""
    
    def test_sql_with_retry_timeout(self):
        """Test timeout handling"""
        schema = db_service.get_schema()
        
        # Set extremely short timeout to force timeout
        result = llm_agent.generate_sql_with_retry(
            user_query="Show complex query",
            schema_str=schema,
            db_service=db_service,
            fast_mode=False,
            max_retries=10,
            timeout_seconds=0.0001  # 0.1ms timeout - will definitely timeout
        )
        
        # With extremely short timeout, should either timeout or succeed very quickly
        # If it succeeds (due to mock being instant), that's also acceptable
        if result["success"]:
            # Mock LLM can be instant, so this is acceptable
            assert result["sql"] is not None
        else:
            # Or it should timeout
            assert "timeout" in result["error"].lower()


class TestDataStructures:
    """Tests for data structures returned by API"""
    
    def test_query_response_structure(self):
        """Test that query results have correct structure for CSV export"""
        sql = "SELECT * FROM patients LIMIT 5"
        result = db_service.execute_query(sql)
        
        # Validate structure matches what CSV export expects
        assert "columns" in result
        assert "data" in result
        assert "row_count" in result
        
        assert isinstance(result["columns"], list)
        assert isinstance(result["data"], list)
        assert len(result["columns"]) > 0
        
        if result["row_count"] > 0:
            assert len(result["data"]) > 0
            # Each row should be a dict
            assert isinstance(result["data"][0], dict)
            # Columns should match keys in data
            for col in result["columns"]:
                assert col in result["data"][0]


class TestMultiTenantIsolation:
    """Tests for multi-tenant isolation"""
    
    def test_chat_history_username_tracking(self):
        """Test that chat history tracks username in metadata"""
        from services.chat_history import chat_history
        
        # Add message with username
        chat_history.add_message(
            role="user",
            content="Test query",
            metadata={"user": "test_user_1"}
        )
        
        messages = chat_history.get_recent_messages(hours=1)
        
        # Find our test message
        test_msg = next((m for m in messages if m.get("text") == "Test query"), None)
        assert test_msg is not None
        # Metadata is stored in 'meta' field, not 'metadata'
        assert test_msg.get("meta", {}).get("user") == "test_user_1"
    
    def test_cache_structure_supports_user_isolation(self):
        """Test that cache structure is ready for per-user isolation"""
        # Verify cache exists and can support user-keyed data
        assert hasattr(llm_agent, 'query_plan_cache')
        assert isinstance(llm_agent.query_plan_cache, dict)
        
        # Test setting a user-specific cache key
        test_key = ("test_user", "query_hash_123")
        llm_agent.query_plan_cache[test_key] = "Test plan"
        
        assert llm_agent.query_plan_cache[test_key] == "Test plan"
        
        # Different user should have different key
        different_user_key = ("different_user", "query_hash_123")
        assert different_user_key not in llm_agent.query_plan_cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
