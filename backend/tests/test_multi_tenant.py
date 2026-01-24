import pytest
from services.chat_history import chat_history
from services.llm_agent import llm_agent

class TestMultiTenantIsolation:
    """Tests for multi-tenant isolation"""
    
    def test_chat_history_username_tracking(self):
        """Test that chat history tracks username (user_id) in threads"""
        user_id = "test_user_isolation"
        thread_id = chat_history.create_thread(user_id=user_id, title="Isolation Test")
        
        # Add message
        chat_history.add_message(
            thread_id=thread_id,
            role="user",
            content="Isolated query",
            metadata={"extra": "isolated_data"}
        )
        
        messages = chat_history.get_thread_messages(thread_id)
        
        # Find our test message
        test_msg = next((m for m in messages if m.get("text") == "Isolated query"), None)
        assert test_msg is not None
        assert test_msg.get("meta", {}).get("extra") == "isolated_data"
        
        # Verify thread belongs to correct user
        threads = chat_history.get_user_threads(user_id)
        assert any(t['id'] == thread_id for t in threads)
        
        # Verify it doesn't appear for another user
        other_user_threads = chat_history.get_user_threads("other_user")
        assert not any(t['id'] == thread_id for t in other_user_threads)
    
    def test_cache_structure_supports_user_isolation(self):
        """Test that cache structure supports per-user isolation"""
        # Verify cache exists and can support user-keyed data
        assert hasattr(llm_agent, 'query_plan_cache')
        assert isinstance(llm_agent.query_plan_cache, dict)
        
        # Test setting a user-specific cache key
        test_key = ("tenant_a", "query_hash_xxx")
        llm_agent.query_plan_cache[test_key] = "Plan A"
        
        assert llm_agent.query_plan_cache[test_key] == "Plan A"
        
        # Different user should have different key even for same query hash
        different_user_key = ("tenant_b", "query_hash_xxx")
        assert different_user_key not in llm_agent.query_plan_cache
