import pytest
from services.database import db_service

def test_db_schema():
    """Test that the database schema can be retrieved and contains expected tables."""
    schema = db_service.get_schema()
    assert schema is not None
    assert "Table: patients" in schema
        
def test_db_query():
    """Test executing a sample query against the database."""
    results = db_service.execute_query("SELECT * FROM patients LIMIT 5")
    assert results is not None
    assert "row_count" in results
    assert results['row_count'] == 5
    assert "columns" in results
    assert "data" in results
