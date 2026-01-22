"""Test script to verify SQL cleaning logic."""

def _clean_sql(raw_sql: str) -> str:
    """
    Clean SQL query by removing common LLM artifacts.
    
    Removes:
    - Prefixes like "Answer:", "SQL:", "Query:", "Here's the query:", etc.
    - Markdown code fences (```sql, ```)
    - Trailing semicolons
    - Leading/trailing whitespace
    - Any text before the first SQL keyword
    """
    sql = raw_sql.strip()
    
    # Remove markdown code fences
    sql = sql.replace("```sql", "").replace("```", "").strip()
    
    # Remove common prefixes (case-insensitive)
    prefixes_to_remove = [
        "answer:", "sql:", "query:", "here's the query:", "here is the query:",
        "here's the sql:", "here is the sql:", "the query is:", "the sql is:",
        "sql query:", "sqlite query:", "response:", "result:"
    ]
    
    sql_lower = sql.lower()
    for prefix in prefixes_to_remove:
        if sql_lower.startswith(prefix):
            sql = sql[len(prefix):].strip()
            sql_lower = sql.lower()
    
    # Remove any text before the first SQL keyword
    sql_keywords = ["SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"]
    for keyword in sql_keywords:
        keyword_lower = keyword.lower()
        idx = sql_lower.find(keyword_lower)
        if idx > 0:
            # Check if there's text before the keyword that's not part of SQL
            before_text = sql[:idx].strip()
            # If there's text before and it doesn't end with a SQL construct, remove it
            if before_text and not before_text.endswith(("(", ",", "=")):
                sql = sql[idx:]
                break
    
    # Remove trailing semicolons
    sql = sql.rstrip(";")
    
    # Final cleanup
    sql = sql.strip()
    
    return sql


# Test cases
test_cases = [
    {
        "input": "Answer: SELECT * FROM patients WHERE state = 'CA'",
        "expected": "SELECT * FROM patients WHERE state = 'CA'"
    },
    {
        "input": "SQL: SELECT COUNT(*) FROM visits",
        "expected": "SELECT COUNT(*) FROM visits"
    },
    {
        "input": "```sql\nSELECT * FROM billing\n```",
        "expected": "SELECT * FROM billing"
    },
    {
        "input": "Here's the query:\nSELECT patient_id, name FROM patients;",
        "expected": "SELECT patient_id, name FROM patients"
    },
    {
        "input": "SELECT * FROM lab_results",
        "expected": "SELECT * FROM lab_results"
    },
    {
        "input": "The SQL is: SELECT state, COUNT(*) FROM patients GROUP BY state",
        "expected": "SELECT state, COUNT(*) FROM patients GROUP BY state"
    },
    {
        "input": "Response: WITH cte AS (SELECT * FROM patients) SELECT * FROM cte",
        "expected": "WITH cte AS (SELECT * FROM patients) SELECT * FROM cte"
    }
]

print("Testing SQL Cleaning Logic\n")
print("=" * 80)

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    result = _clean_sql(test["input"])
    success = result == test["expected"]
    
    if success:
        passed += 1
        status = "✓ PASS"
    else:
        failed += 1
        status = "✗ FAIL"
    
    print(f"\nTest {i}: {status}")
    print(f"Input:    '{test['input'][:60]}...'")
    print(f"Expected: '{test['expected']}'")
    print(f"Got:      '{result}'")
    if not success:
        print(f"  >>> Mismatch!")

print("\n" + "=" * 80)
print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
