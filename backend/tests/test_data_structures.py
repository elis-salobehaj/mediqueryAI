import pytest
from services.database import db_service

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
