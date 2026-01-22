"""
LangGraph Multi-Agent SQL Generation Workflow

This module implements a multi-agent architecture for complex SQL generation
using specialized agents coordinated by LangGraph state machine.

Agents:
- Schema Navigator: Selects relevant tables and join paths
- SQL Writer: Generates SQL from schema context and query plan  
- Critic: Validates SQL semantically using different LLM for diverse perspective

Architecture follows DIN-SQL pattern with cross-model reflection.
"""

import time
import logging
import os
from typing import TypedDict, Annotated, Sequence, Literal
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

# Conditional imports with graceful degradation
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GOOGLE = True
except ImportError:
    logger.warning("langchain-google-genai not available")
    HAS_GOOGLE = False

try:
    from langchain_anthropic import ChatAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    logger.warning("langchain-anthropic not available")
    HAS_ANTHROPIC = False

try:
    from langchain_ollama import ChatOllama
    HAS_OLLAMA = True
except ImportError:
    logger.warning("langchain-ollama not available")
    HAS_OLLAMA = False

try:
    from langchain_aws import ChatBedrockConverse
    HAS_BEDROCK = True
except ImportError:
    logger.warning("langchain-aws not available")
    HAS_BEDROCK = False


class AgentState(TypedDict):
    """Shared state for multi-agent SQL generation workflow."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    original_query: str
    username: str | None
    query_plan: str | None
    selected_tables: list[str]
    table_schemas: dict[str, str]  # table_name -> schema description
    generated_sql: str | None
    validation_result: dict | None
    reflections: list[str]
    attempt_count: int
    max_attempts: int
    timeout_seconds: float
    start_time: float
    thoughts: list[str]  # For UI transparency
    agent_mode: str  # "multi-agent"
    previous_sqls: list[str]  # Track generated SQL to detect duplicates


class MultiAgentSQLGenerator:
    """
    LangGraph-based multi-agent SQL generation system.
    
    Uses specialized agents for schema navigation, SQL writing, and validation
    to handle complex schemas (50+ tables) with cross-model critique.
    """
    
    def __init__(
        self,
        database_service,
        llm_agent,
        config: dict | None = None
    ):
        self.db_service = database_service
        self.llm_agent = llm_agent  # Reuse existing LLMAgent for schema retrieval
        
        # Configuration
        default_config = {
            "timeout_seconds": 120,
            "max_attempts": 3,
            "schema_navigator_model": os.getenv("SCHEMA_NAVIGATOR_MODEL", "qwen2.5-coder:7b"),
            "sql_writer_model": os.getenv("SQL_WRITER_MODEL", "sqlcoder:7b"),
            "critic_model": os.getenv("CRITIC_MODEL", "llama3.1"),
            "use_ollama": os.getenv("USE_LOCAL_MODEL", "true").lower() == "true",
            "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "use_bedrock": os.getenv("USE_BEDROCK", "false").lower() == "true",
            "bedrock_region": os.getenv("AWS_BEDROCK_REGION", "us-west-2"),
            "bedrock_sql_writer_model": os.getenv("BEDROCK_SQL_WRITER_MODEL", "us.anthropic.claude-sonnet-4-5-20250514-v1:0"),
            "bedrock_navigator_model": os.getenv("BEDROCK_NAVIGATOR_MODEL", "us.anthropic.claude-haiku-4-5-20250514-v1:0"),
            "bedrock_critic_model": os.getenv("BEDROCK_CRITIC_MODEL", "us.anthropic.claude-haiku-4-5-20250514-v1:0"),
        }
        self.config = {**default_config, **(config or {})}
        
        # Initialize LLMs
        self._init_llms()
        
        # Build workflow graph
        self.graph = self._create_graph()
    
    def _init_llms(self):
        """Initialize LangChain LLMs for each agent."""
        google_api_key = os.getenv("GEMINI_API_KEY")
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        bedrock_token = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
        use_ollama = self.config["use_ollama"]
        use_bedrock = self.config["use_bedrock"]
        ollama_host = self.config["ollama_host"]
        
        # Priority 1: Use local Ollama models (default)
        if use_ollama and HAS_OLLAMA:
            logger.info(f"Using Ollama models for multi-agent workflow at {ollama_host}")
            
            # Schema Navigator LLM
            try:
                self.schema_navigator_llm = ChatOllama(
                    model=self.config["schema_navigator_model"],
                    base_url=ollama_host,
                    temperature=0.0,
                )
                logger.info(f"Schema Navigator: {self.config['schema_navigator_model']}")
            except Exception as e:
                logger.error(f"Failed to initialize Schema Navigator with Ollama: {e}")
                self.schema_navigator_llm = None
            
            # SQL Writer LLM
            try:
                self.sql_writer_llm = ChatOllama(
                    model=self.config["sql_writer_model"],
                    base_url=ollama_host,
                    temperature=0.0,
                )
                logger.info(f"SQL Writer: {self.config['sql_writer_model']}")
            except Exception as e:
                logger.error(f"Failed to initialize SQL Writer with Ollama: {e}")
                self.sql_writer_llm = None
            
            # Critic LLM (different model for diverse perspective)
            try:
                self.critic_llm = ChatOllama(
                    model=self.config["critic_model"],
                    base_url=ollama_host,
                    temperature=0.3,  # Higher temp for diverse critique
                )
                logger.info(f"Critic: {self.config['critic_model']}")
            except Exception as e:
                logger.error(f"Failed to initialize Critic with Ollama: {e}")
                self.critic_llm = None
        
        # Priority 2: AWS Bedrock with Bearer Token
        elif use_bedrock and HAS_BEDROCK and bedrock_token:
            logger.info(f"Using AWS Bedrock with Bearer Token auth in {self.config['bedrock_region']}")
            
            try:
                # boto3 auto-detects AWS_BEARER_TOKEN_BEDROCK env var
                self.schema_navigator_llm = ChatBedrockConverse(
                    model_id=self.config["bedrock_navigator_model"],
                    region_name=self.config["bedrock_region"],
                    temperature=0.0,
                )
                logger.info(f"Schema Navigator: {self.config['bedrock_navigator_model']}")
            except Exception as e:
                logger.error(f"Failed to initialize Schema Navigator with Bedrock: {e}")
                self.schema_navigator_llm = None
            
            try:
                self.sql_writer_llm = ChatBedrockConverse(
                    model_id=self.config["bedrock_sql_writer_model"],
                    region_name=self.config["bedrock_region"],
                    temperature=0.0,
                )
                logger.info(f"SQL Writer: {self.config['bedrock_sql_writer_model']}")
            except Exception as e:
                logger.error(f"Failed to initialize SQL Writer with Bedrock: {e}")
                self.sql_writer_llm = None
            
            try:
                self.critic_llm = ChatBedrockConverse(
                    model_id=self.config["bedrock_critic_model"],
                    region_name=self.config["bedrock_region"],
                    temperature=0.3,
                )
                logger.info(f"Critic: {self.config['bedrock_critic_model']}")
            except Exception as e:
                logger.error(f"Failed to initialize Critic with Bedrock: {e}")
                self.critic_llm = None
        
        # Priority 3: Fall back to cloud models if Ollama/Bedrock disabled or unavailable
        else:
            logger.info("Using cloud models for multi-agent workflow")
            
            # Schema Navigator LLM
            if HAS_GOOGLE and google_api_key:
                self.schema_navigator_llm = ChatGoogleGenerativeAI(
                    model=self.config["schema_navigator_model"],
                    api_key=google_api_key,
                    temperature=0.0,
                )
            else:
                logger.warning("Google API not available for Schema Navigator")
                self.schema_navigator_llm = None
            
            # SQL Writer LLM
            if HAS_GOOGLE and google_api_key:
                self.sql_writer_llm = ChatGoogleGenerativeAI(
                    model=self.config["sql_writer_model"],
                    api_key=google_api_key,
                    temperature=0.0,
                )
            else:
                logger.warning("Google API not available for SQL Writer")
                self.sql_writer_llm = None
            
            # Critic LLM (different model for diverse perspective)
            if HAS_ANTHROPIC and anthropic_api_key:
                self.critic_llm = ChatAnthropic(
                    model=self.config["critic_model"],
                    api_key=anthropic_api_key,
                    temperature=0.0,
                )
            elif HAS_GOOGLE and google_api_key:
                # Fallback to Google with different temperature
                logger.info("Using Google Gemini for Critic (Anthropic not available)")
                self.critic_llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    api_key=google_api_key,
                    temperature=0.3,  # Higher temp for diverse critique
                )
            else:
                logger.warning("No LLM available for Critic agent")
                self.critic_llm = None
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph state machine for multi-agent workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("schema_navigator", self._schema_navigator_node)
        workflow.add_node("sql_writer", self._sql_writer_node)
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("reflect", self._reflect_node)
        
        # Define edges
        workflow.set_entry_point("schema_navigator")
        workflow.add_edge("schema_navigator", "sql_writer")
        workflow.add_edge("sql_writer", "critic")
        
        # Conditional edge: retry, success, or terminate
        workflow.add_conditional_edges(
            "critic",
            self._should_continue,
            {
                "retry": "reflect",
                "success": END,
                "max_attempts": END,
                "timeout": END,
            }
        )
        
        workflow.add_edge("reflect", "sql_writer")
        
        return workflow.compile()
    
    def _schema_navigator_node(self, state: AgentState) -> AgentState:
        """
        Agent 1: Schema Navigator
        
        Analyzes natural language query and selects relevant tables/columns.
        Handles complex schemas (50+ tables) with multi-hop join path discovery.
        """
        # Early timeout check
        if time.time() - state["start_time"] > state["timeout_seconds"]:
            state["thoughts"].append("Timeout reached, skipping Schema Navigator")
            return state
        
        state["thoughts"].append("[1] Schema Navigator: Analyzing query and selecting tables...")
        
        try:
            # Use existing semantic retrieval from LLMAgent
            if hasattr(self.llm_agent, 'retrieve_relevant_tables'):
                relevant_tables = self.llm_agent.retrieve_relevant_tables(
                    state["original_query"]
                )
                state["selected_tables"] = relevant_tables
                table_list = ", ".join(relevant_tables[:5])
                if len(relevant_tables) > 5:
                    table_list += f" (+{len(relevant_tables)-5} more)"
                state["thoughts"].append(f"[2] Schema Navigator: Selected {len(relevant_tables)} tables: {table_list}")
            else:
                # Fallback: use all tables
                tables = self.db_service.get_all_table_names()
                state["selected_tables"] = tables
                state["thoughts"].append(f"[2] Schema Navigator: Using all {len(tables)} tables (semantic retrieval unavailable)")
            
            # Get schemas for selected tables
            table_schemas = {}
            for table_name in state["selected_tables"]:
                schema = self.db_service.get_table_schema(table_name)
                if schema:
                    # Format as string for LLM consumption
                    columns_str = ", ".join([f"{col} {dtype}" for col, dtype in schema])
                    table_schemas[table_name] = f"CREATE TABLE {table_name} ({columns_str})"
            
            state["table_schemas"] = table_schemas
            
            # Add explicit table names to thoughts for clarity
            if table_schemas:
                table_names_list = ", ".join(table_schemas.keys())
                thought_num = len(state["thoughts"]) + 1
                state["thoughts"].append(f"[{thought_num}] Schema Navigator: Table schemas prepared for: {table_names_list}")
            
            # Generate message for next agent
            schema_summary = "\n".join([
                f"- {table}: {schema}"
                for table, schema in table_schemas.items()
            ])
            
            state["messages"].append(AIMessage(
                content=f"Schema Navigator selected {len(table_schemas)} relevant tables:\n{schema_summary}",
                name="schema_navigator"
            ))
            
        except Exception as e:
            logger.error(f"Schema Navigator error: {e}", exc_info=True)
            state["thoughts"].append(f"Schema Navigator error: {str(e)}")
            # Continue anyway with empty schemas
            state["selected_tables"] = []
            state["table_schemas"] = {}
        
        return state
    
    def _sql_writer_node(self, state: AgentState) -> AgentState:
        """
        Agent 2: SQL Writer
        
        Generates SQL based on schema context and query plan.
        Specializes in complex aggregations and window functions.
        """
        # Early timeout check
        if time.time() - state["start_time"] > state["timeout_seconds"]:
            state["thoughts"].append("Timeout reached, skipping SQL Writer")
            return state
        
        attempt = state["attempt_count"] + 1
        thought_num = len(state["thoughts"]) + 1
        
        # Show schema context preview for debugging
        schema_preview = ""
        if state["table_schemas"]:
            first_schema = list(state["table_schemas"].values())[0][:80]
            schema_preview = f" | Schema preview: {first_schema}..."
        
        state["thoughts"].append(f"[{thought_num}] SQL Writer: Generating SQL (Attempt {attempt}){schema_preview}")
        
        if not self.sql_writer_llm:
            logger.error("SQL Writer LLM not available")
            state["generated_sql"] = None
            return state
        
        try:
            # Build prompt with schema context and reflections
            # Schema already has "CREATE TABLE table_name (...)" so don't duplicate
            schema_context = "\n\n".join([
                schema
                for table, schema in state["table_schemas"].items()
            ])
            
            reflections_context = ""
            if state["reflections"]:
                reflections_context = "\n\nPrevious attempts failed with these issues:\n" + "\n".join([
                    f"{i+1}. {ref}" for i, ref in enumerate(state["reflections"])
                ])
            
            query_plan_context = ""
            if state["query_plan"]:
                query_plan_context = f"\n\nQuery Plan:\n{state['query_plan']}"
            
            # Build list of exact table names for emphasis
            table_names_list = list(state["table_schemas"].keys())
            table_names_str = ", ".join(table_names_list)
            
            system_prompt = f"""You are an expert SQL generator. Generate a SQLite query to answer the user's question.

=== DATABASE SCHEMA ===
{schema_context}

!!! CRITICAL: TABLE NAMES ARE CASE-SENSITIVE AND MUST BE EXACT !!!

AVAILABLE TABLES (use EXACTLY as shown):
{table_names_str}

DO NOT USE THESE INCORRECT NAMES:
❌ patient (table is called 'patients' with an 's')
❌ visit (table is called 'visits' with an 's')
❌ bill (table is called 'billing')
❌ patient_visit (this table does not exist)
❌ patient_data (this table does not exist)
❌ sales (this table does not exist)

CORRECT EXAMPLES:
✓ SELECT * FROM patients WHERE state = 'CA'
✓ SELECT * FROM visits WHERE visit_date > '2024-01-01'
✓ SELECT * FROM billing WHERE amount > 100
✓ SELECT * FROM lab_results WHERE glucose_level > 150

INCORRECT EXAMPLES (will fail):
✗ SELECT * FROM patient WHERE state = 'CA' (no table called 'patient')
✗ SELECT * FROM visit WHERE date > '2024-01-01' (no table called 'visit')

REMEMBER: Use 'patients' not 'patient', 'visits' not 'visit', 'billing' not 'bill'!
{query_plan_context}
{reflections_context}

Rules:
1. Return ONLY the SQL query, no explanations or prefixes like "Answer:" or "SQL:"
2. Do NOT include markdown code fences like ```sql
3. Use proper JOIN syntax when combining tables
4. Handle NULL values appropriately
5. Use aggregations (SUM, AVG, COUNT) when appropriate
6. Do NOT include semicolons at the end
7. For complex queries, use CTEs (WITH clause) for clarity
8. Start directly with SELECT, WITH, INSERT, UPDATE, DELETE, or CREATE
9. ALWAYS use the exact table names from the schema above - do NOT invent or modify table names"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Question: {state['original_query']}\n\nREMINDER: Available tables are: {table_names_str}\nUse EXACT table names from the schema. For patient data use 'patients' not 'patient'.")
            ]
            
            # Debug logging to see prompt
            logger.debug(f"SQL Writer prompt (first 500 chars): {system_prompt[:500]}...")
            logger.debug(f"Available tables: {table_names_str}")
            
            response = self.sql_writer_llm.invoke(messages)
            raw_sql = response.content.strip()
            
            # Enhanced SQL cleaning to remove common LLM artifacts
            sql = self._clean_sql(raw_sql)
            
            # Get valid tables from schema
            valid_tables = set(state["table_schemas"].keys())
            
            # Auto-correct common table name hallucinations
            sql_corrected = sql
            corrections_made = []
            
            # Map of common incorrect names to correct names
            table_corrections = {
                r'\bpatient\b': 'patients',  # patient -> patients
                r'\bvisit\b': 'visits',      # visit -> visits
                r'\bbill\b': 'billing',      # bill -> billing
                r'\bpatient_visit\b': 'visits',  # patient_visit -> visits
                r'\bpatient_data\b': 'patients',  # patient_data -> patients
                r'\blabs\b': 'lab_results',  # labs -> lab_results
                r'\bresult\b': 'lab_results',  # result -> lab_results (if not result_id etc)
                r'\bsales\b': 'billing',  # sales -> billing
            }
            
            import re
            for pattern, replacement in table_corrections.items():
                # Only replace if the incorrect table is actually in valid_tables as the correct version
                if re.search(pattern, sql_corrected, re.IGNORECASE):
                    # Check if replacement table actually exists in schema
                    if replacement in valid_tables:
                        original_sql = sql_corrected
                        # Use case-insensitive replacement but preserve FROM/JOIN context
                        sql_corrected = re.sub(
                            pattern,
                            replacement,
                            sql_corrected,
                            flags=re.IGNORECASE
                        )
                        if sql_corrected != original_sql:
                            incorrect_name = re.search(pattern, original_sql, re.IGNORECASE).group()
                            corrections_made.append(f"{incorrect_name} -> {replacement}")
            
            if corrections_made:
                thought_num = len(state["thoughts"]) + 1
                state["thoughts"].append(f"[{thought_num}] SQL Writer: Auto-corrected table names: {', '.join(corrections_made)}")
                sql = sql_corrected
            
            # Defensive validation: check for table name mismatches
            sql_upper = sql.upper()
            tables_in_sql = set()
            for word in sql.split():
                word_clean = word.strip('(),;').lower()
                if word_clean in {t.lower() for t in valid_tables}:
                    tables_in_sql.add(word_clean)
            
            # Check for common hallucinated table names
            hallucinated_tables = []
            for hallucinated in ['patient ', 'visit ', 'bill ', 'patient_visit', 'patient_data', 'labs ', 'results ']:
                if hallucinated.upper() in sql_upper + ' ':
                    hallucinated_tables.append(hallucinated.strip())
            
            state["generated_sql"] = sql
            
            # Track SQL for deduplication
            if "previous_sqls" not in state:
                state["previous_sqls"] = []
            state["previous_sqls"].append(sql)
            
            thought_num = len(state["thoughts"]) + 1
            # Show SQL snippet and table usage for transparency
            sql_preview = sql[:100].replace('\n', ' ')
            if len(sql) > 100:
                sql_preview += "..."
            
            tables_used_str = ", ".join(sorted(tables_in_sql)) if tables_in_sql else "none detected"
            state["thoughts"].append(f"[{thought_num}] SQL Writer: Generated SQL ({len(sql)} chars), using tables: {tables_used_str}")
            
            if hallucinated_tables:
                thought_num = len(state["thoughts"]) + 1
                state["thoughts"].append(f"[{thought_num}] SQL Writer WARNING: Detected potentially invalid table names: {', '.join(hallucinated_tables)}")
            
            state["messages"].append(AIMessage(
                content=f"SQL Writer generated query:\n```sql\n{sql}\n```",
                name="sql_writer"
            ))
            
        except Exception as e:
            logger.error(f"SQL Writer error: {e}", exc_info=True)
            thought_num = len(state["thoughts"]) + 1
            state["thoughts"].append(f"[{thought_num}] SQL Writer error: {str(e)}")
            state["generated_sql"] = None
        
        return state
    
    def _clean_sql(self, raw_sql: str) -> str:
        """
        Clean SQL query by removing common LLM artifacts.
        
        Removes:
        - Special tokens like <s>, </s>, <|endoftext|>
        - Prefixes like "Answer:", "SQL:", "Query:", "Here's the query:", etc.
        - Markdown code fences (```sql, ```)
        - Trailing semicolons
        - Leading/trailing whitespace
        - Any text before the first SQL keyword
        - Comments and explanatory text
        """
        sql = raw_sql.strip()
        
        # Remove special tokens from LLM models (e.g., <s>, </s>, <|endoftext|>)
        import re
        sql = re.sub(r'<\|?[a-z]+\|?>', '', sql, flags=re.IGNORECASE)  # Remove <s>, </s>, <|endoftext|>, etc.
        sql = sql.replace('<s>', '').replace('</s>', '').strip()
        
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
        
        # Remove comments and explanatory text (lines starting with #)
        lines = sql.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line.startswith('#') and line:  # Skip comment lines
                cleaned_lines.append(line)
        sql = '\n'.join(cleaned_lines)
        
        # Remove any text before the first SQL keyword
        sql_keywords = ["SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"]
        for keyword in sql_keywords:
            keyword_lower = keyword.lower()
            idx = sql.lower().find(keyword_lower)
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
    
    def _critic_node(self, state: AgentState) -> AgentState:
        """
        Agent 3: Critic
        
        Validates SQL semantically and provides actionable feedback.
        Uses different LLM for diverse perspective (cross-model critique).
        """
        # Early timeout check
        if time.time() - state["start_time"] > state["timeout_seconds"]:
            state["thoughts"].append("Timeout reached, skipping Critic")
            return state
        
        thought_num = len(state["thoughts"]) + 1
        state["thoughts"].append(f"[{thought_num}] Critic: Validating SQL...")
        
        if not state["generated_sql"]:
            state["validation_result"] = {
                "valid": False,
                "error": "No SQL generated",
                "row_count": 0,
                "warnings": []
            }
            return state
        
        try:
            # 1. Syntax validation via EXPLAIN
            validation = self.db_service.validate_sql(state["generated_sql"])
            thought_num = len(state["thoughts"]) + 1
            
            # 2. Semantic validation via Critic LLM
            if validation["valid"] and self.critic_llm:
                semantic_critique = self._get_semantic_critique(
                    state["original_query"],
                    state["generated_sql"],
                    state["table_schemas"]
                )
                
                # Add semantic critique to validation
                if semantic_critique.get("has_issues"):
                    validation["warnings"].append(semantic_critique["critique"])
                    state["thoughts"].append(f"[{thought_num}] Critic: Found semantic issues - {semantic_critique['critique'][:80]}...")
                else:
                    state["thoughts"].append(f"[{thought_num}] Critic: SQL is valid ({validation.get('row_count', 0)} rows, no semantic issues)")
            elif validation["valid"]:
                state["thoughts"].append(f"[{thought_num}] Critic: SQL is syntactically valid ({validation.get('row_count', 0)} rows)")
            else:
                state["thoughts"].append(f"[{thought_num}] Critic: SQL validation failed - {validation.get('error', 'Unknown error')}")
            
            state["validation_result"] = validation
            
            # Generate message
            if validation["valid"]:
                msg = f"Critic: SQL is syntactically valid (returns {validation.get('row_count', '?')} rows)"
            else:
                msg = f"Critic: SQL validation failed - {validation['error']}"
            
            state["messages"].append(AIMessage(
                content=msg,
                name="critic"
            ))
            
        except Exception as e:
            logger.error(f"Critic error: {e}", exc_info=True)
            state["thoughts"].append(f"Critic error: {str(e)}")
            state["validation_result"] = {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "row_count": 0,
                "warnings": []
            }
        
        state["attempt_count"] += 1
        return state
    
    def _get_semantic_critique(
        self,
        query: str,
        sql: str,
        table_schemas: dict
    ) -> dict:
        """Use Critic LLM to validate semantic correctness."""
        try:
            schema_context = "\n".join([
                f"{table}: {schema}"
                for table, schema in table_schemas.items()
            ])
            
            prompt = f"""You are a SQL expert validator. Analyze if this SQL query correctly answers the user's question.

User Question: {query}

Generated SQL:
```sql
{sql}
```

Database Schema:
{schema_context}

Does this SQL correctly answer the question? Check for:
1. Are the right tables joined?
2. Are the right columns selected?
3. Are filters/conditions correct?
4. Are aggregations appropriate?

Respond in JSON format:
{{"has_issues": true/false, "critique": "explanation if has_issues is true, else empty string"}}"""
            
            response = self.critic_llm.invoke([HumanMessage(content=prompt)])
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response.content.strip())
                return result
            except json.JSONDecodeError:
                # Fallback: assume no issues if can't parse
                return {"has_issues": False, "critique": ""}
                
        except Exception as e:
            logger.error(f"Semantic critique error: {e}")
            return {"has_issues": False, "critique": ""}
    
    def _reflect_node(self, state: AgentState) -> AgentState:
        """
        Generate reflection from validation failure.
        
        Analyzes error and provides specific guidance for next attempt.
        """
        thought_num = len(state["thoughts"]) + 1
        state["thoughts"].append(f"[{thought_num}] Reflecting on error...")
        
        validation = state["validation_result"]
        if not validation:
            return state
        
        # Generate reflection message with specific guidance
        error_msg = validation.get("error", "Unknown error")
        warnings = validation.get("warnings", [])
        
        reflection = f"Attempt {state['attempt_count']} failed: {error_msg}"
        if warnings:
            reflection += f"\nWarnings: {', '.join(warnings)}"
        
        # Add specific guidance based on error type
        if "syntax error" in error_msg.lower():
            reflection += "\nTip: Check for proper SQL syntax, ensure no extra text in query"
        elif "no such table" in error_msg.lower():
            reflection += "\nTip: Verify table names match the schema exactly"
        elif "no such column" in error_msg.lower():
            reflection += "\nTip: Check column names against the table schema"
        
        state["reflections"].append(reflection)
        thought_num = len(state["thoughts"]) + 1
        state["thoughts"].append(f"[{thought_num}] Reflection: {reflection}")
        
        state["messages"].append(AIMessage(
            content=f"Reflection: {reflection}",
            name="reflector"
        ))
        
        return state
    
    def _should_continue(self, state: AgentState) -> Literal["retry", "success", "max_attempts", "timeout"]:
        """
        Determine next step based on validation result.
        
        Returns:
            - "success": SQL is valid and has reasonable results
            - "retry": SQL failed validation, retry
            - "max_attempts": Hit retry limit
            - "timeout": Exceeded time limit
        """
        # 1. ALWAYS check timeout first
        elapsed = time.time() - state["start_time"]
        if elapsed > state["timeout_seconds"]:
            state["thoughts"].append(f"Timeout: {elapsed:.1f}s > {state['timeout_seconds']}s")
            return "timeout"
        
        # 2. ALWAYS check max_attempts second
        if state["attempt_count"] >= state["max_attempts"]:
            state["thoughts"].append(f"Max attempts reached: {state['attempt_count']}")
            return "max_attempts"
        
        # 3. Check for SQL deduplication
        if state["generated_sql"] and state["generated_sql"] in state.get("previous_sqls", [])[:-1]:
            state["thoughts"].append("Same SQL generated twice, stopping retry")
            return "max_attempts"
        
        # 4. Check validation result
        validation = state["validation_result"]
        if not validation:
            return "retry"
        
        # 5. Success/retry based on validation
        if validation.get("valid"):
            row_count = validation.get("row_count", 0)
            thought_num = len(state["thoughts"]) + 1
            
            # Accept zero rows for COUNT/aggregate queries
            if row_count == 0:
                query_lower = state["original_query"].lower()
                if any(kw in query_lower for kw in ["count", "how many", "total", "sum", "average", "avg"]):
                    state["thoughts"].append(f"[{thought_num}] ✓ Success: Valid SQL with 0 rows (aggregate query)")
                    return "success"
            
            # Accept any valid result with rows >= 0
            if row_count >= 0:
                state["thoughts"].append(f"[{thought_num}] ✓ Success: Valid SQL with {row_count} rows")
                return "success"
        
        return "retry"
    
    async def ainvoke(self, query: str, username: str | None = None) -> dict:
        """
        Execute multi-agent workflow asynchronously.
        
        Args:
            query: Natural language question
            username: User identifier for multi-tenant isolation
            
        Returns:
            dict with sql, data, thoughts, metadata
        """
        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "original_query": query,
            "username": username,
            "query_plan": None,  # Could add plan generation as first step
            "selected_tables": [],
            "table_schemas": {},
            "generated_sql": None,
            "validation_result": None,
            "reflections": [],
            "attempt_count": 0,
            "max_attempts": self.config["max_attempts"],
            "timeout_seconds": self.config["timeout_seconds"],
            "start_time": time.time(),
            "thoughts": [],
            "agent_mode": "multi-agent",
            "previous_sqls": [],
        }
        
        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            
            # Extract results
            sql = final_state.get("generated_sql")
            validation = final_state.get("validation_result") or {}
            
            # Execute SQL if valid
            data = None
            error = None
            if sql and validation.get("valid"):
                try:
                    result = self.db_service.execute_query(sql)
                    data = result
                except Exception as e:
                    error = str(e)
                    logger.error(f"SQL execution error: {e}")
            else:
                error = validation.get("error", "SQL generation failed")
            
            return {
                "sql": sql,
                "data": data,
                "error": error,
                "thoughts": final_state["thoughts"],
                "agent_mode": "multi-agent",
                "agents_used": ["schema_navigator", "sql_writer", "critic"],
                "attempts": final_state["attempt_count"],
                "reflections": final_state["reflections"],
                "selected_tables": final_state["selected_tables"],
            }
            
        except Exception as e:
            logger.error(f"Multi-agent workflow error: {e}", exc_info=True)
            return {
                "sql": None,
                "data": None,
                "error": f"Multi-agent workflow error: {str(e)}",
                "thoughts": [f"Error: {str(e)}"],
                "agent_mode": "multi-agent",
                "agents_used": [],
                "attempts": 0,
                "reflections": [],
                "selected_tables": [],
            }
