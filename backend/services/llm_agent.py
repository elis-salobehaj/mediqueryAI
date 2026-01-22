import anthropic
import os
import logging
from typing import Optional, Dict, Any, List
import json

logger = logging.getLogger(__name__)

# Conditional Google GenAI Import
try:
    from google import genai
    from google.genai import types
    from google.api_core import exceptions
    HAS_GOOGLE_GENAI = True
except ImportError:
    logger.warning("google-genai not available. Google GenAI features disabled.")
    HAS_GOOGLE_GENAI = False
    genai = None
    types = None
    exceptions = None

# Conditional Ollama Import
try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    logger.warning("ollama not available. Local model features disabled.")
    HAS_OLLAMA = False
    ollama = None

# Conditional Bedrock Import
try:
    from langchain_aws import ChatBedrockConverse
    HAS_BEDROCK = True
except ImportError:
    logger.warning("langchain-aws not available. Bedrock features disabled.")
    HAS_BEDROCK = False

# Conditional LlamaIndex Imports
try:
    from llama_index.core import SQLDatabase, VectorStoreIndex, Settings
    from llama_index.core.objects import SQLTableNodeMapping, ObjectIndex, SQLTableSchema
    from llama_index.llms.ollama import Ollama
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from sqlalchemy import create_engine
    HAS_LLAMA_INDEX = True
except ImportError:
    logger.warning("LlamaIndex or dependencies not found. Semantic features disabled.")
    HAS_LLAMA_INDEX = False

class LLMAgent:
    def __init__(self):
        self.api_key = None
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.anthropic_client = None
        self.model = None
        self.use_local = os.getenv('USE_LOCAL_MODEL', 'false').lower() == 'true'
        self.local_model = os.getenv('LOCAL_MODEL_NAME', 'qwen3:latest')
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.use_bedrock = os.getenv('USE_BEDROCK', 'false').lower() == 'true'
        self.bedrock_region = os.getenv('AWS_BEDROCK_REGION', 'us-west-2')
        self.bedrock_sql_writer = os.getenv('BEDROCK_SQL_WRITER_MODEL', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        self.bedrock_navigator = os.getenv('BEDROCK_NAVIGATOR_MODEL', 'anthropic.claude-3-5-haiku-20241022-v1:0')
        self.bedrock_critic = os.getenv('BEDROCK_CRITIC_MODEL', 'anthropic.claude-3-5-haiku-20241022-v1:0')
        self.bedrock_client = None
        self.last_thoughts = []
        
        # Multi-Tenant Isolation: Query plan cache will be keyed by (username, query_hash) in Phase 3
        # Current isolation: Chat history tracks username in metadata (see chat_history.add_message)
        self.query_plan_cache = {}  # Placeholder for Phase 3 caching
        
        # Safety Settings - Block None for medical data analysis (only for Google GenAI)
        if HAS_GOOGLE_GENAI and types:
            self.safety_settings = [
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
            ]
        else:
            self.safety_settings = []
        
        if self.use_local:
            logger.info(f"Using local Ollama model: {self.local_model}")
        elif self.use_bedrock and HAS_BEDROCK:
            # Initialize Bedrock client for single agent mode
            try:
                bedrock_token = os.getenv('AWS_BEARER_TOKEN_BEDROCK')
                if bedrock_token:
                    # boto3 auto-detects AWS_BEARER_TOKEN_BEDROCK env var
                    self.bedrock_client = ChatBedrockConverse(
                        model_id=self.bedrock_sql_writer,
                        region_name=self.bedrock_region,
                        temperature=0.0,
                    )
                    logger.info(f"Using AWS Bedrock model: {self.bedrock_sql_writer}")
                else:
                    logger.warning("AWS_BEARER_TOKEN_BEDROCK not set. Bedrock features disabled.")
            except Exception as e:
                logger.error(f"Failed to initialize Bedrock client: {e}")
                self.bedrock_client = None
        else:
            if self.anthropic_key:
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
                logger.info("Anthropic client initialized")

        # Semantic Retrieval Components
        self.sql_retriever = None
        self._setup_semantic_engine()

    def _setup_semantic_engine(self):
        """Initializes LlamaIndex ObjectIndex for semantic table retrieval."""
        if not HAS_LLAMA_INDEX:
            return

        try:
            self.last_thoughts.append("Initializing Semantic Engine...")
            # Use the persistent DB file created by DatabaseService
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = f"sqlite:///{os.path.join(base_dir, 'medical.db')}"
            
            engine = create_engine(db_path)
            sql_database = SQLDatabase(engine)
            
            # Load metadata
            meta_path = os.path.join(base_dir, "data", "semantic_metadata.json")
            table_descriptions = {}
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                    for item in meta:
                        table_descriptions[item['table_name']] = item['description']

            # Create Table Schema Objects
            table_node_mapping = SQLTableNodeMapping(sql_database)
            table_schema_objs = []
            for table_name in sql_database.get_usable_table_names():
                table_schema_objs.append(
                    SQLTableSchema(
                        table_name=table_name, 
                        context_str=table_descriptions.get(table_name, "Medical data table")
                    )
                )

            # Initialize Embedding Model (Local)
            Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
            
            # Create Object Index
            self.obj_index = ObjectIndex.from_objects(
                table_schema_objs,
                table_node_mapping,
                VectorStoreIndex,
            )
            self.sql_retriever = self.obj_index.as_retriever(similarity_top_k=3)
            logger.info("Semantic SQL Retriever initialized.")
            
        except Exception as e:
            logger.error(f"Failed to setup semantic engine: {e}")
            self.sql_retriever = None

    def configure(self, api_key: str):
        """Configures the Gemini API client."""
        if self.use_local:
            logger.info("Local model mode enabled - API key not required")
            return
        
        if not HAS_GOOGLE_GENAI or not genai:
            logger.warning("Google GenAI not available. Skipping API key configuration.")
            return
            
        self.api_key = api_key
        # genai.configure(api_key=self.api_key) # Old way
        self.client = genai.Client(api_key=self.api_key)
        # self.model = genai.GenerativeModel('gemma-3-27b-it', safety_settings=self.safety_settings) # Old way
        self.model_id = 'gemini-1.5-flash' # Using a known stable model for now, 'gemma-3' might be specific
        logger.info("Configured Google Gemini API (v2 Client)")

    def get_available_models(self) -> list:
        """Returns a list of available models based on configuration."""
        if self.use_local:
            return [
                {"id": "qwen2.5-coder:7b", "name": "Qwen 2.5 Coder (7B) - RECOMMENDED"},
                {"id": "sqlcoder:7b", "name": "Defog SQLCoder (7B)"},
                {"id": "llama3.1", "name": "Llama 3.1 (8B)"},
                {"id": "qwen3:latest", "name": "Qwen 3 (7B)"},
            ]
        elif self.use_bedrock:
            # Return Bedrock models with user-friendly names
            return [
                {
                    "id": self.bedrock_sql_writer,
                    "name": "Claude 3.5 Sonnet v2 (SQL Writer) - RECOMMENDED"
                },
                {
                    "id": self.bedrock_navigator,
                    "name": "Claude 3.5 Haiku (Schema Navigator)"
                },
                {
                    "id": self.bedrock_critic,
                    "name": "Claude 3.5 Haiku (Critic)"
                },
            ]
        else:
            return [
                {"id": "gemma-3-27b-it", "name": "GEMMA 3 27B (DEFAULT / HIGH QUOTA)"},
                {"id": "gemini-2.5-flash-lite", "name": "GEMINI 2.5 FLASH LITE"},
                {"id": "claude-3-5-sonnet-20241022", "name": "CLAUDE 3.5 SONNET (ANTHROPIC)"},
            ]

    def set_model(self, model_id: str):
        """Switches the active model."""
        if self.use_local:
            # Allow switching local models if they are in the supported list
            supported_local = [m['id'] for m in self.get_available_models()]
            if model_id in supported_local:
                self.local_model = model_id
                logger.info(f"Switched local model to: {model_id}")
            else:
                logger.warning(f"Attempted to switch to unsupported local model: {model_id}. Keeping {self.local_model}")
            return

        # Handle Bedrock Models
        if self.use_bedrock and 'anthropic' in model_id:
            self.model = model_id
            logger.info(f"Switched Bedrock model to: {model_id}")
            return

        # Handle Anthropic Models
        if 'claude' in model_id:
            if not self.anthropic_client:
                 logger.warning("Anthropic API Key not found. Please set ANTHROPIC_API_KEY.")
            self.model = model_id # Just store the ID for dispatch
            logger.info(f"Switched model to: {model_id}")
            return

        # Handle Gemini Models
        if not self.api_key:
             raise ValueError("Google API Key not configured.")
        
        # In Google GenAI v2, we just use the model ID string with the client
        self.model = model_id
        logger.info(f"Switched model to: {model_id}")

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama model."""
        if not HAS_OLLAMA or not ollama:
            raise ValueError("Ollama not available. Install with: pip install ollama")
        
        try:
            response = ollama.chat(
                model=self.local_model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': 0.1,  # Lower temperature for more consistent SQL
                    'num_predict': 500   # Max tokens
                }
            )
            return response['message']['content'].strip()
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            logger.error(f"Make sure Ollama is running and model '{self.local_model}' is installed")
            logger.error(f"Install with: ollama pull {self.local_model}")
            raise e

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Cloud API."""
        if not self.anthropic_client:
            raise ValueError("Anthropic API Key not configured. Set ANTHROPIC_API_KEY in .env")
        
        try:
            model_id = self.model if isinstance(self.model, str) and 'claude' in self.model else 'claude-3-5-sonnet-20241022'
            message = self.anthropic_client.messages.create(
                model=model_id,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise e

    def _call_bedrock(self, prompt: str) -> str:
        """Call AWS Bedrock API using ChatBedrockConverse."""
        if not self.bedrock_client:
            raise ValueError("Bedrock client not initialized. Check AWS_BEARER_TOKEN_BEDROCK in .env")
        
        try:
            from langchain_core.messages import HumanMessage
            
            # Use the current model if set, otherwise default to SQL writer
            model_id = self.model if isinstance(self.model, str) and 'anthropic' in self.model else self.bedrock_sql_writer
            
            # Update client model if needed
            if self.bedrock_client.model_id != model_id:
                self.bedrock_client = ChatBedrockConverse(
                    model_id=model_id,
                    region_name=self.bedrock_region,
                    temperature=0.0,
                )
            
            response = self.bedrock_client.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.error(f"Bedrock API call failed: {e}")
            raise e

    def generate_sql(self, user_query: str, schema_str: str, history: list = None) -> Optional[str]:
        """Converts natural language query to SQL based on the schema and history."""
        # Format history for context
        history_context = ""
        if history:
            # Take last 5 messages, excluding the current one if it's already there
            relevant_history = history[-5:] 
            history_str = "\n".join([f"{msg['role']}: {msg['text']}" for msg in relevant_history])
            history_context = f"Chat History:\n{history_str}\n\n"

        # Reset thoughts for this new query
        self.last_thoughts = []
        self.last_thoughts.append(f"Analyzing user request: '{user_query}'")

        # SCHEMA SELECTION STRATEGY
        selected_schema = schema_str # Default to full schema
        
        if self.sql_retriever:
             self.last_thoughts.append("Using Semantic Search to identify relevant tables...")
             try:
                 nodes = self.sql_retriever.retrieve(user_query)
                 if nodes:
                     table_names = [node.table_name for node in nodes]
                     self.last_thoughts.append(f"Identified tables: {', '.join(table_names)}")
                     
                     # Filter the full schema string (rough heuristic or query DB)
                     # Since we have full schema_str passed in, we can try to filter it, 
                     # OR just rely on the full schema if it's small.
                     # For this implementation, let's trust the full schema if small, 
                     # but if we wanted to enforce, we'd rebuild schema_str.
                     # Given the current 4 tables, full schema is fine, but the *Thinking* is valuable.
                     
                     # Check if we should fallback to full schema?
                     pass
             except Exception as e:
                 logger.error(f"Semantic retrieval failed: {e}")
                 self.last_thoughts.append(f"Semantic retrieval failed({str(e)}), using full schema.")

        self.last_thoughts.append("Retrieving database schema...")
        self.last_thoughts.append(f"Context loaded: Full Schema ({len(schema_str)} chars)")
        
        prompt = f"""
You are an expert SQLite developer. Convert the following natural language request into a valid SQL query.
The database has the following schema:
{schema_str}

{history_context}
User Request: {user_query}

Rules:
1. Return ONLY the SQL query. No markdown formatting (no ```sql), no explanation.
2. The query must be valid SQLite.
3. If the user asks for something that cannot be answered by the schema, or asks for something unrelated, return "NO_MATCH".
4. Use standard SQLite functions.
5. **IMPORTANT - Case-Insensitive Text Matching**:
   - For text comparisons, ALWAYS use LIKE with wildcards for case-insensitive matching
   - Example: Instead of WHERE chronic_condition = 'diabetes', use WHERE chronic_condition LIKE '%diabetes%'
   - This handles case variations (Diabetes, diabetes, DIABETES, DiAbEtEs)
   - Apply this to ALL text column filters (names, conditions, diagnoses, etc.)
6. When filtering by text values, always use LIKE '%value%' pattern for flexibility.
7. **IMPORTANT - Display Patient Names, Not IDs**:
   - When querying patient data, ALWAYS SELECT the 'name' column instead of 'patient_id'
   - If you need to join tables, use patient_id for the JOIN but SELECT the name for display
   - Example: SELECT p.name, v.diagnosis FROM patients p JOIN visits v ON p.patient_id = v.patient_id
   - Never show patient_id in the final results unless explicitly asked for IDs
8. **Context Awareness**:
   - If the request is a follow-up (e.g., "which of them...", "show me the details"), use the Chat History to infer context.
   - You may need to incorporate filters or IDs from previous queries shown in history.
9. **Typo Tolerance & Fuzzy Matching**:
   - The user may make typos in table names (e.g., 'patiens' -> 'patients'), column names (e.g., 'outstandign' -> 'outstanding_balance'), or values.
   - You MUST intelligently infer the correct table or column based on the provided schema.
   - Do NOT fail if a simple typo is present; correct it and generate the valid SQL.
10. **Schema Hints & Search Strategy**:
    - **Demographics Only (e.g. "count patients by state", "age distribution")**: Query ONLY the 'patients' table. Do NOT join 'visits' or 'billing' unless the query explicitly asks for visit/financial details.
    - **Searching for an Illness/Disease**: If the user asks about a specific condition (e.g. 'diabetes') without specifying source:
        - You MUST search **BOTH** `patients.chronic_condition` AND `visits.diagnosis`.
        - Use `LEFT JOIN visits v ON p.patient_id = v.patient_id`.
        - Use `WHERE (p.chronic_condition LIKE '%term%' OR v.diagnosis LIKE '%term%')`.
        - Use `SELECT DISTINCT ...` to avoid duplicates.
    - **Billing / Revenue**: Found in 'billing' table. Join 'billing' with 'visits' on 'visit_id', then 'visits' with 'patients' on 'patient_id'.
User Request: {user_query}
"""
        logger.debug(f"Generating SQL with model: {self.model}")
        model_display = self.local_model if self.use_local else ('Bedrock' if self.use_bedrock else 'Cloud API')
        self.last_thoughts.append(f"Selected Model: {model_display}")
        self.last_thoughts.append("Generating SQL query...")
        try:
            if self.use_local:
                sql = self._call_ollama(prompt)
            elif self.use_bedrock and self.bedrock_client:
                # AWS Bedrock Case
                sql = self._call_bedrock(prompt)
            elif isinstance(self.model, str) and 'claude' in self.model: 
                # Anthropic Case
                sql = self._call_anthropic(prompt)
            else:
                # Google Gemini Case
                if not HAS_GOOGLE_GENAI or not genai:
                    raise ValueError("Google GenAI not available. Install with: pip install google-genai")
                
                if not hasattr(self, 'client') or not self.client:
                     # Re-init default if needed
                     if self.api_key:
                         self.client = genai.Client(api_key=self.api_key)
                     else:
                         raise ValueError("Google Client not initialized")

                # Use self.model which might be a string ID now, or self.model_id
                target_model = self.model if isinstance(self.model, str) else 'gemini-1.5-flash'
                
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        safety_settings=self.safety_settings
                    )
                )
                sql = response.text.strip()
            
            logger.debug(f"Raw LLM Response: {sql}")

            # Cleanup if the model adds markdown despite instructions
            if sql.startswith("```"):
                sql = sql.strip("`").replace("sql", "").strip()
            
            logger.debug(f"Cleaned SQL: {sql}")
            self.last_thoughts.append(f"Generated SQL: {sql}")
            return sql
        except exceptions.ResourceExhausted:
            logger.warning("Google API Rate Limit Exceeded")
            return "RATE_LIMIT"
        except exceptions.InvalidArgument:
            logger.error("Google API Invalid Argument (Check API Key)")
            return "INVALID_KEY"
        except exceptions.GoogleAPICallError as e:
            logger.error(f"Google API Error: {e}")
            return f"API_ERROR: {str(e)}"
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return None

    def generate_insight(self, user_query: str, data: Dict[str, Any], history: list = None) -> str:
        """Generates a natural language insight/response based on the data."""
        try:
            data_preview = str(data['data'])[:5000]
            row_count = data['row_count']
        except:
             data_preview = "No data"
             row_count = 0
             
        prompt = (
            f"You are a healthcare data expert. The user asked: '{user_query}'\\n"
            f"We executed a SQL query and got the following data (truncated if too large):\\n"
            f"{data_preview}\\n"
            f"Row count: {row_count}\\n"
            f"Your task:\\n"
            f"1. Answer the user's question clearly.\\n"
            f"2. Identify potential patterns or KPI insights if visible.\\n"
            f"3. If the data is empty, suggest what might be wrong or how to refine the query.\\n"
            f"4. If the data corresponds to the question, perform a brief analysis.\\n"
            f"Keep the response helpful, professional, and within 3-4 sentences unless more detail is needed."
        )

        try:
            if self.use_local:
                return self._call_ollama(prompt)
            elif self.use_bedrock and self.bedrock_client:
                return self._call_bedrock(prompt)
            elif isinstance(self.model, str) and 'claude' in self.model:
                return self._call_anthropic(prompt)
            else:
                if not HAS_GOOGLE_GENAI or not genai:
                    return "Analyzed data (GenAI not available for detailed insights)."
                
                if not hasattr(self, 'client') or not self.client:
                     self.client = genai.Client(api_key=self.api_key)
                
                target_model = self.model if isinstance(self.model, str) else 'gemini-1.5-flash'
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(safety_settings=self.safety_settings)
                )
                return response.text.strip()
        except Exception as e:
            if HAS_GOOGLE_GENAI and exceptions and isinstance(e, exceptions.ResourceExhausted):
                return "Analyzed data, but couldn't generate detailed insight due to API rate limits (quota exceeded)."
            logger.error(f"Insight generation failed: {e}")
            return "I have the data but couldn't generate a summary insight."

    def determine_visualization(self, user_query: str, data: Dict[str, Any]) -> str:
        """Determines the best visualization type for the data using heuristics and LLM."""
        if data['row_count'] == 0:
            return "table"

        columns = data.get('columns', [])
        rows = data.get('data', [])
        row_count = data['row_count']
        
        # Helper: Check if column is numeric
        def is_numeric_col(col_name: str) -> bool:
            try:
                return isinstance(rows[0][col_name], (int, float))
            except:
                return False
        
        numeric_cols = [col for col in columns if is_numeric_col(col)]
        categorical_cols = [col for col in columns if not is_numeric_col(col)]
        
        # ===== HEURISTIC RULES (Fast path) =====
        
        # Geographic data → choropleth/scattergeo
        if any('state' in col.lower() or 'country' in col.lower() for col in columns):
            return "choropleth"
        
        # Single row → indicator/table
        if row_count == 1:
            return "indicator" if len(numeric_cols) > 0 else "table"
        
        # Time series detection → line/area
        if any('date' in col.lower() or 'time' in col.lower() for col in columns):
            if len(numeric_cols) >= 1:
                return "line"
        
        # 3+ numeric columns → 3D scatter/surface/parcoords
        if len(numeric_cols) >= 3:
            if row_count < 100:
                return "scatter3d"
            elif row_count < 500:
                return "parcoords"
            else:
                return "heatmap"
        
        # 2 columns (1 categorical, 1 numeric) → bar/pie
        if len(columns) == 2 and len(categorical_cols) == 1 and len(numeric_cols) == 1:
            if row_count <= 10:
                return "pie"
            elif row_count <= 50:
                return "bar"
            else:
                return "histogram"
        
        # Hierarchical data (3+ categorical) → sunburst/treemap
        if len(categorical_cols) >= 3:
            return "sunburst"
        
        # Distribution queries → box/violin/histogram
        query_lower = user_query.lower()
        if any(kw in query_lower for kw in ['distribution', 'spread', 'quartile', 'outlier']):
            return "box"
        if 'frequency' in query_lower or 'count' in query_lower:
            return "histogram"
        if 'correlation' in query_lower or 'relationship' in query_lower:
            if len(numeric_cols) >= 2:
                return "heatmap" if len(numeric_cols) > 4 else "scatter"
        if 'flow' in query_lower or 'journey' in query_lower or 'path' in query_lower:
            return "sankey"
        if 'trend' in query_lower or 'over time' in query_lower:
            return "line"
        if 'compare' in query_lower or 'comparison' in query_lower:
            return "bar"
        if 'total' in query_lower or 'sum' in query_lower or 'kpi' in query_lower:
            return "indicator"
        if 'gauge' in query_lower or 'score' in query_lower or 'rating' in query_lower:
            return "gauge"
        
        # ===== LLM-BASED SELECTION (Fallback) =====
        prompt = f"""
You are a data visualization expert. Choose the BEST Plotly.js chart type for this query and data.

User Query: "{user_query}"
Data Columns: {columns}
Row Count: {row_count}
Numeric Columns: {numeric_cols}
Categorical Columns: {categorical_cols}
Sample Data: {str(rows[:2])}

Available Chart Types (choose ONE):

**Basic**: bar, pie, donut, line, scatter, area
**Statistical**: box, violin, histogram, heatmap, contour
**Financial**: waterfall, funnel, candlestick, ohlc
**3D**: scatter3d, surface, mesh3d
**Maps**: choropleth, scattergeo, scattermapbox
**Hierarchical**: sunburst, treemap, icicle, sankey
**Specialized**: indicator, gauge, parcoords, splom, table

Guidelines:
- bar: categorical comparison (e.g., "count by state")
- pie/donut: parts of whole (e.g., "distribution by gender")
- line/area: trends over time
- scatter: correlation between 2 numeric variables
- box/violin: distribution analysis, outliers
- histogram: frequency distribution
- heatmap: correlation matrix (3+ numeric cols)
- scatter3d: 3D relationships (3+ numeric cols)
- choropleth: geographic data (state/country columns)
- sunburst/treemap: hierarchical categories (3+ categorical)
- sankey: flow/journey analysis
- indicator/gauge: single KPI value
- parcoords: multi-dimensional analysis (4+ numeric)
- splom: scatter plot matrix (3-4 numeric cols)
- waterfall: cumulative effects
- funnel: conversion rates
- table: raw data, complex structures

Return ONLY the chart type name (lowercase, no explanation).
"""
        try:
            if self.use_local:
                vis_type = self._call_ollama(prompt).lower()
            else:
                if not hasattr(self, 'client') or not self.client:
                    return "table"
                
                target_model = self.model if isinstance(self.model, str) else 'gemini-1.5-flash'
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=prompt
                )
                vis_type = response.text.strip().lower()
            
            # Validate response
            valid_types = [
                'bar', 'pie', 'donut', 'line', 'scatter', 'area',
                'box', 'violin', 'histogram', 'heatmap', 'contour', 'histogram2d',
                'waterfall', 'funnel', 'candlestick', 'ohlc',
                'scatter3d', 'surface', 'mesh3d', 'cone', 'line3d',
                'choropleth', 'scattergeo', 'scattermapbox', 'choroplethmapbox', 'densitymapbox',
                'sunburst', 'treemap', 'icicle', 'sankey',
                'indicator', 'gauge', 'bullet', 'parcoords', 'splom',
                'scatterpolar', 'barpolar', 'scatterternary',
                'pointcloud', 'streamtube', 'isosurface', 'volume',
                'heatmapgl', 'scattergl', 'scatter3dgl',
                'table', 'map'
            ]
            
            # Handle aliases
            if vis_type == 'map':
                vis_type = 'choropleth'
            
            if vis_type in valid_types:
                return vis_type
            else:
                logger.warning(f"LLM returned invalid chart type: {vis_type}, defaulting to table")
                return "table"
        except Exception as e:
            logger.error(f"Vis Type determination failed: {e}")
            return "table"

    def generate_query_plan(self, user_query: str, schema_str: str) -> str:
        """
        Stage 2: Plan Construction - Generates a natural language query plan before SQL generation.
        
        Returns a step-by-step plan explaining what the SQL query should do.
        """
        self.last_thoughts.append("Generating query plan...")
        
        prompt = f"""
You are a database query planner. Given the user's request and database schema, create a step-by-step plan (in natural language) for how to construct the SQL query.

Database Schema:
{schema_str}

User Request: {user_query}

Create a concise plan with 2-5 steps that explains:
1. Which tables to use
2. How to join them (if needed)
3. What filters to apply
4. What to select/aggregate
5. Any ordering or grouping needed

Example format:
"Step 1: Query the patients table to get patient demographics.
Step 2: Join with visits table on patient_id to access visit diagnoses.
Step 3: Filter for records where diagnosis contains 'diabetes' (case-insensitive).
Step 4: Select patient names and visit dates.
Step 5: Order by visit date descending."

Return ONLY the plan steps, no additional commentary.
"""
        
        try:
            if self.use_local:
                plan = self._call_ollama(prompt)
            elif isinstance(self.model, str) and 'claude' in self.model:
                plan = self._call_anthropic(prompt)
            else:
                if not HAS_GOOGLE_GENAI or not genai:
                    return "Step 1: Query the database (GenAI not available for detailed planning)."
                
                if not hasattr(self, 'client') or not self.client:
                    self.client = genai.Client(api_key=self.api_key)
                
                target_model = self.model if isinstance(self.model, str) else 'gemini-1.5-flash'
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(safety_settings=self.safety_settings)
                )
                plan = response.text.strip()
            
            self.last_thoughts.append(f"Query Plan: {plan}")
            return plan
            
        except Exception as e:
            logger.error(f"Query plan generation failed: {e}")
            return "Unable to generate query plan - proceeding with direct SQL generation"

    def reflect_on_error(self, failed_sql: str, error_msg: str, user_query: str, query_plan: str = None) -> str:
        """
        Reflexion: Analyzes why a SQL query failed and suggests corrections.
        
        Returns a verbal critique and suggested fix.
        """
        self.last_thoughts.append(f"Reflecting on error: {error_msg[:100]}...")
        
        plan_context = f"\nOriginal Query Plan:\n{query_plan}\n" if query_plan else ""
        
        prompt = f"""
You are a SQL debugging expert. A query failed and you need to analyze why and suggest a fix.

User's Original Request: {user_query}
{plan_context}
Failed SQL Query:
{failed_sql}

Error Message:
{error_msg}

Analyze what went wrong and provide:
1. A brief explanation of the error (1-2 sentences)
2. What specifically needs to be corrected

Be concise and actionable. Return your analysis as plain text.
"""
        
        try:
            if self.use_local:
                reflection = self._call_ollama(prompt)
            elif isinstance(self.model, str) and 'claude' in self.model:
                reflection = self._call_anthropic(prompt)
            else:
                if not HAS_GOOGLE_GENAI or not genai:
                    return "Unable to reflect on SQL error (GenAI not available)."
                
                if not hasattr(self, 'client') or not self.client:
                    self.client = genai.Client(api_key=self.api_key)
                
                target_model = self.model if isinstance(self.model, str) else 'gemini-1.5-flash'
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(safety_settings=self.safety_settings)
                )
                reflection = response.text.strip()
            
            return reflection
            
        except Exception as e:
            logger.error(f"Reflection generation failed: {e}")
            return f"Error analysis unavailable. Original error: {error_msg}"

    def generate_sql_with_retry(
        self,
        user_query: str,
        schema_str: str,
        db_service,
        history: list = None,
        fast_mode: bool = False,
        max_retries: int = 3,
        timeout_seconds: int = 60
    ) -> dict:
        """
        Stage 4: Reflexion Loop - Generates SQL with self-correction retry mechanism.
        
        Returns:
            dict with keys:
                - sql (str | None): Final SQL query
                - success (bool): True if query validated successfully
                - attempts (int): Number of attempts made
                - reflections (list[str]): Self-critiques from failed attempts
                - query_plan (str | None): Natural language query plan
                - error (str | None): Final error message if all attempts failed
        """
        import time
        
        start_time = time.time()
        attempts = []
        reflections = []
        query_plan = None
        
        # Stage 2: Plan Construction (skip if fast_mode)
        if not fast_mode:
            try:
                query_plan = self.generate_query_plan(user_query, schema_str)
            except Exception as e:
                logger.warning(f"Plan generation failed, continuing without plan: {e}")
                self.last_thoughts.append("Plan generation failed - using direct SQL generation")
        else:
            self.last_thoughts.append("Fast mode enabled - skipping plan construction")
        
        # Stage 3 & 4: SQL Generation with Reflexion Loop
        for attempt_num in range(max_retries):
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                error_msg = f"Query exceeded {timeout_seconds}s timeout after {attempt_num + 1} attempts"
                self.last_thoughts.append(error_msg)
                return {
                    "sql": None,
                    "success": False,
                    "attempts": attempt_num + 1,
                    "reflections": reflections,
                    "query_plan": query_plan,
                    "error": error_msg
                }
            
            self.last_thoughts.append(f"Attempt {attempt_num + 1}/{max_retries}")
            
            # Generate SQL (with plan context if available)
            if query_plan and not fast_mode:
                # Enhance the prompt with the plan
                enhanced_history = (history or []) + [{
                    "role": "system",
                    "text": f"Query Plan: {query_plan}"
                }]
                sql = self.generate_sql(user_query, schema_str, enhanced_history)
            else:
                sql = self.generate_sql(user_query, schema_str, history)
            
            if not sql or sql in ["NO_MATCH", "RATE_LIMIT", "INVALID_KEY"] or sql.startswith("API_ERROR"):
                error_msg = f"SQL generation failed: {sql}"
                attempts.append({"sql": sql, "error": error_msg})
                return {
                    "sql": None,
                    "success": False,
                    "attempts": attempt_num + 1,
                    "reflections": reflections,
                    "query_plan": query_plan,
                    "error": error_msg
                }
            
            # Validate SQL
            validation = db_service.validate_sql(sql)
            attempts.append({"sql": sql, "validation": validation})
            
            # Check if valid and passes sanity checks
            if validation["valid"]:
                row_count = validation.get("row_count", 0)
                warnings = validation.get("warnings", [])
                
                # Success criteria: valid SQL with reasonable row count
                if row_count > 0 and row_count <= 10000:
                    self.last_thoughts.append(f"✓ Query validated successfully ({row_count} rows)")
                    if warnings:
                        self.last_thoughts.append(f"Warnings: {', '.join(warnings)}")
                    return {
                        "sql": sql,
                        "success": True,
                        "attempts": attempt_num + 1,
                        "reflections": reflections,
                        "query_plan": query_plan,
                        "error": None
                    }
                
                # Query is valid but has issues (0 rows or too many rows)
                if row_count == 0:
                    issue = "Query returns 0 rows - may need different filters or table"
                elif row_count > 10000:
                    issue = f"Query returns {row_count} rows - may need additional filters"
                else:
                    issue = "Query validation concern"
                
                self.last_thoughts.append(f"⚠ {issue}")
                
                # If this is the last attempt, return it anyway since it's syntactically valid
                if attempt_num == max_retries - 1:
                    self.last_thoughts.append("Final attempt - accepting query despite warnings")
                    return {
                        "sql": sql,
                        "success": True,
                        "attempts": attempt_num + 1,
                        "reflections": reflections,
                        "query_plan": query_plan,
                        "error": None
                    }
                
                # Try to improve the query
                error_msg = issue
            else:
                # SQL is invalid
                error_msg = validation.get("error", "Unknown validation error")
                self.last_thoughts.append(f"✗ Validation failed: {error_msg[:100]}")
            
            # Reflect on the error and try again (unless this was the last attempt)
            if attempt_num < max_retries - 1:
                reflection = self.reflect_on_error(sql, error_msg, user_query, query_plan)
                reflections.append(reflection)
                self.last_thoughts.append(f"Reflection: {reflection[:150]}...")
                
                # Add reflection to history for next attempt
                if not history:
                    history = []
                history.append({
                    "role": "system",
                    "text": f"Previous attempt failed: {error_msg}. Reflection: {reflection}"
                })
        
        # All attempts failed
        final_error = f"Failed after {max_retries} attempts. Last error: {error_msg}"
        self.last_thoughts.append(final_error)
        return {
            "sql": None,
            "success": False,
            "attempts": max_retries,
            "reflections": reflections,
            "query_plan": query_plan,
            "error": final_error
        }

llm_agent = LLMAgent()
