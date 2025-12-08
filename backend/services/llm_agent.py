import google.generativeai as genai
import ollama
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LLMAgent:
    def __init__(self):
        self.api_key = None
        self.model = None
        self.use_local = os.getenv('USE_LOCAL_MODEL', 'false').lower() == 'true'
        self.local_model = os.getenv('LOCAL_MODEL_NAME', 'qwen2.5:3b')
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        
        if self.use_local:
            logger.info(f"Using local Ollama model: {self.local_model}")
        else:
            logger.info("Using Google Gemini API")

    def configure(self, api_key: str):
        """Configures the Gemini API client."""
        if self.use_local:
            logger.info("Local model mode enabled - API key not required")
            return
            
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-flash-latest')
        logger.info("Configured Google Gemini API")

    def set_model(self, model_id: str):
        """Switches the active model."""
        if self.use_local:
            logger.warning(f"Local mode enabled - ignoring model switch to {model_id}")
            return
            
        if not self.api_key:
             raise ValueError("API Key not configured.")
        try:
            self.model = genai.GenerativeModel(model_id)
            logger.info(f"Switched model to: {model_id}")
        except Exception as e:
            logger.error(f"Failed to switch model to {model_id}: {e}")
            self.model = genai.GenerativeModel('gemini-flash-latest')

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama model."""
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

    def generate_sql(self, user_query: str, schema_str: str) -> Optional[str]:
        """Converts natural language query to SQL based on the schema."""
        prompt = f"""
You are an expert SQLite developer. Convert the following natural language request into a valid SQL query.
The database has the following schema:
{schema_str}

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

User Request: {user_query}
"""
        try:
            if self.use_local:
                sql = self._call_ollama(prompt)
            else:
                if not self.model:
                    raise ValueError("API Key not configured.")
                response = self.model.generate_content(prompt)
                sql = response.text.strip()
            
            # Cleanup if the model adds markdown despite instructions
            if sql.startswith("```"):
                sql = sql.strip("`").replace("sql", "").strip()
            return sql
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return None

    def generate_insight(self, user_query: str, data: Dict[str, Any]) -> str:
        """Generates a natural language insight/response based on the data."""
        data_preview = str(data['data'])[:5000]
        
        prompt = f"""
You are a healthcare data expert. The user asked: "{user_query}"
We executed a SQL query and got the following data (truncated if too large):
{data_preview}
Row count: {data['row_count']}

Your task:
1. Answer the user's question clearly.
2. Identify potential patterns or KPI insights if visible.
3. If the data is empty, suggest what might be wrong or how to refine the query.
4. If the data corresponds to the question, perform a brief analysis.

Keep the response helpful, professional, and within 3-4 sentences unless more detail is needed.
"""
        try:
            if self.use_local:
                return self._call_ollama(prompt)
            else:
                if not self.model:
                    raise ValueError("API Key not configured.")
                response = self.model.generate_content(prompt)
                return response.text.strip()
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return "Could not generate insight due to an error."

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
                if not self.model:
                    return "table"
                response = self.model.generate_content(prompt)
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

llm_agent = LLMAgent()
