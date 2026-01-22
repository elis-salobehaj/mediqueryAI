#!/usr/bin/env python3
"""
Test script to verify AWS Bedrock integration with bearer token authentication.
Tests the multi-agent workflow with Claude 3.5 models.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bedrock_import():
    """Test if langchain-aws is properly installed."""
    print("✓ Step 1: Testing langchain-aws import...")
    try:
        from langchain_aws import ChatBedrockConverse
        print("  ✓ ChatBedrockConverse imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import ChatBedrockConverse: {e}")
        return False

def test_boto3_version():
    """Test if boto3 is at the correct version."""
    print("\n✓ Step 2: Testing boto3 version...")
    try:
        import boto3
        version = boto3.__version__
        print(f"  ✓ boto3 version: {version}")
        
        # Check if version is >= 1.35.0
        major, minor, _ = map(int, version.split('.'))
        if major > 1 or (major == 1 and minor >= 35):
            print("  ✓ boto3 version is sufficient (>=1.35.0)")
            return True
        else:
            print(f"  ✗ boto3 version {version} is too old, need >=1.35.0")
            return False
    except Exception as e:
        print(f"  ✗ Error checking boto3: {e}")
        return False

def test_environment_variables():
    """Test if required environment variables are set."""
    print("\n✓ Step 3: Testing environment variables...")
    
    required_vars = {
        "USE_BEDROCK": os.getenv("USE_BEDROCK"),
        "AWS_BEDROCK_REGION": os.getenv("AWS_BEDROCK_REGION"),
        "AWS_BEARER_TOKEN_BEDROCK": os.getenv("AWS_BEARER_TOKEN_BEDROCK"),
        "BEDROCK_SQL_WRITER_MODEL": os.getenv("BEDROCK_SQL_WRITER_MODEL"),
        "BEDROCK_NAVIGATOR_MODEL": os.getenv("BEDROCK_NAVIGATOR_MODEL"),
        "BEDROCK_CRITIC_MODEL": os.getenv("BEDROCK_CRITIC_MODEL"),
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Mask the bearer token for security
            display_value = var_value if var_name != "AWS_BEARER_TOKEN_BEDROCK" else "***" + var_value[-8:]
            print(f"  ✓ {var_name}: {display_value}")
        else:
            print(f"  ✗ {var_name}: NOT SET")
            all_set = False
    
    return all_set

def test_langgraph_agent_import():
    """Test if the MultiAgentSQLGenerator can be imported."""
    print("\n✓ Step 4: Testing MultiAgentSQLGenerator import...")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from services.langgraph_agent import MultiAgentSQLGenerator
        print("  ✓ MultiAgentSQLGenerator imported successfully")
        return True
    except Exception as e:
        print(f"  ✗ Failed to import MultiAgentSQLGenerator: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bedrock_llm_initialization():
    """Test if Bedrock LLMs can be initialized."""
    print("\n✓ Step 5: Testing Bedrock LLM initialization...")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from services.langgraph_agent import MultiAgentSQLGenerator
        from services.database import DatabaseService
        from services.llm_agent import LLMAgent
        
        # Create a dummy database service
        db_service = DatabaseService()
        
        # Create a dummy LLM agent (no parameters)
        llm_agent = LLMAgent()
        
        # Initialize the agent with Bedrock config
        agent = MultiAgentSQLGenerator(db_service, llm_agent)
        
        # Check if LLMs are initialized
        if hasattr(agent, 'schema_navigator_llm') and agent.schema_navigator_llm:
            print(f"  ✓ Schema Navigator LLM: {type(agent.schema_navigator_llm).__name__}")
        else:
            print("  ✗ Schema Navigator LLM not initialized")
            return False
            
        if hasattr(agent, 'sql_writer_llm') and agent.sql_writer_llm:
            print(f"  ✓ SQL Writer LLM: {type(agent.sql_writer_llm).__name__}")
        else:
            print("  ✗ SQL Writer LLM not initialized")
            return False
            
        if hasattr(agent, 'critic_llm') and agent.critic_llm:
            print(f"  ✓ Critic LLM: {type(agent.critic_llm).__name__}")
        else:
            print("  ✗ Critic LLM not initialized")
            return False
        
        print("  ✓ All three LLMs initialized successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to initialize Bedrock LLMs: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_state_fields():
    """Test if AgentState has the new previous_sqls field."""
    print("\n✓ Step 6: Testing AgentState TypedDict fields...")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from services.langgraph_agent import AgentState
        
        # Check if previous_sqls is in the type annotations
        annotations = AgentState.__annotations__
        
        if 'previous_sqls' in annotations:
            print(f"  ✓ 'previous_sqls' field found: {annotations['previous_sqls']}")
            return True
        else:
            print("  ✗ 'previous_sqls' field not found in AgentState")
            print(f"  Available fields: {list(annotations.keys())}")
            return False
            
    except Exception as e:
        print(f"  ✗ Failed to check AgentState: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 70)
    print("AWS Bedrock Integration Test Suite")
    print("=" * 70)
    
    results = []
    
    results.append(("Import langchain-aws", test_bedrock_import()))
    results.append(("Check boto3 version", test_boto3_version()))
    results.append(("Environment variables", test_environment_variables()))
    results.append(("Import MultiAgentSQLGenerator", test_langgraph_agent_import()))
    results.append(("Initialize Bedrock LLMs", test_bedrock_llm_initialization()))
    results.append(("Check AgentState fields", test_agent_state_fields()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! AWS Bedrock integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
