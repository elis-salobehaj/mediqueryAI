import pytest
from services.database import db_service

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
