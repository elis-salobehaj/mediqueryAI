from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
from contextlib import asynccontextmanager
import asyncio

from services.database import db_service
from services.llm_agent import llm_agent

# Configure Logging
# Configure Logging
log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ],
    force=True
)
logger = logging.getLogger(__name__)
# Force Reload Trigger

from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root (one level up from backend/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Models
class QueryRequest(BaseModel):
    question: str
    model_id: str = "gemma-3-27b-it" # Default to High Quota model 

class QueryResponse(BaseModel):
    sql: str
    data: dict
    insight: str
    visualization_type: str = "table" # 'bar', 'pie', 'line', 'scatter', 'map', 'table'
    error: str = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load data
    logger.info("Initializing application and loading data...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "YOUR_API_KEY" in api_key:
        logger.warning("GEMINI_API_KEY not set in .env")
    else:
        llm_agent.configure(api_key)
    
    # Prune history on startup
    try:
        from services.chat_history import chat_history
        chat_history.prune_old_messages()
        logger.info("Chat history pruned on startup.")
    except Exception as e:
        logger.warning(f"Failed to prune history: {e}")
    
    # Start background task to prune history periodically (every hour)
    async def prune_history_periodically():
        """Background task to prune expired chat history every hour."""
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
            try:
                chat_history.prune_old_messages()
                logger.info("Periodic chat history pruning completed.")
            except Exception as e:
                logger.error(f"Periodic history pruning failed: {e}")
    
    prune_task = asyncio.create_task(prune_history_periodically())
        
    yield
    
    # Shutdown: Cancel background task
    prune_task.cancel()
    try:
        await prune_task
    except asyncio.CancelledError:
        logger.info("Background pruning task cancelled.")
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from services.chat_history import chat_history

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    from datetime import datetime
    return {
        "status": "healthy",
        "service": "antigravity-backend",
        "timestamp": datetime.now().isoformat(),
        "tables": db_service.get_schema().count("Table:")
    }

@app.get("/history")
async def get_history():
    """Returns recent chat messages."""
    messages = chat_history.get_recent_messages()
    return {"messages": messages}

@app.post("/query", response_model=QueryResponse)
def query_data(request: QueryRequest = Body(...)):
    try:
        # 1. Save User Message
        chat_history.add_message(role="user", content=request.question)

        # 2. Ensure configured
        if not llm_agent.api_key:
             api_key = os.getenv("GEMINI_API_KEY")
             if api_key and "YOUR_API_KEY" not in api_key:
                 llm_agent.configure(api_key)
             else:
                raise HTTPException(status_code=500, detail="Backend configuration error: API Key missing.")

        # 3. Get Schema
        schema = db_service.get_schema()

        # 4. Generate SQL (Pass model_id)
        if request.model_id:
            llm_agent.set_model(request.model_id)
        
        sql_query = llm_agent.generate_sql(request.question, schema)
        
        if sql_query == "RATE_LIMIT":
            chat_history.add_message(role="bot", content="Google API Rate Limit Exceeded. Please try again in a minute.")
            return QueryResponse(
                sql="",
                data={"row_count": 0, "columns": [], "data": []},
                insight="**Rate Limit Exceeded**: The Google Gemini API is temporarily blocking requests due to high traffic/quota. Please wait 1-2 minutes and try again, or switch to a local model.",
                error="Rate Limit Exceeded",
                visualization_type="table"
            )

        if sql_query == "INVALID_KEY":
             chat_history.add_message(role="bot", content="Google API Key is invalid.")
             return QueryResponse(
                sql="",
                data={"row_count": 0, "columns": [], "data": []},
                insight="**Configuration Error**: The Google Gemini API Key appears to be invalid or expired. Please check your `.env` file.",
                error="Invalid API Key",
                visualization_type="table"
             )
        
        if sql_query and sql_query.startswith("API_ERROR"):
             chat_history.add_message(role="bot", content="External API Error.")
             return QueryResponse(
                sql="",
                data={"row_count": 0, "columns": [], "data": []},
                insight=f"**API Error**: {sql_query}",
                error=sql_query,
                visualization_type="table"
             )

        if not sql_query or sql_query == "NO_MATCH":
            chat_history.add_message(role="bot", content="I couldn't find relevant data.")
            return QueryResponse(
                sql="",
                data={"row_count": 0, "columns": [], "data": []}, 
                insight="I'm sorry, I couldn't find relevant data in the database to answer your question. Please try asking about patients, visits, or billing.",
                visualization_type="table"
            )

        # 5. Execute SQL
        try:
            results = db_service.execute_query(sql_query)
            if not results: results = {"row_count": 0, "columns": [], "data": []}
        except Exception as e:
            logger.error(f"SQL Execution Error: {e}")
            chat_history.add_message(role="bot", content=f"Database Error: {str(e)}")
            return QueryResponse(
                sql=sql_query,
                data={"row_count": 0, "columns": [], "data": []},
                insight=f"I generated a query but it failed to execute. Error: {str(e)}",
                error=str(e),
                visualization_type="table"
            )

        # 6. Determine Visualization Type
        vis_type = llm_agent.determine_visualization(request.question, results)

        # 7. Generate Insight
        insight = llm_agent.generate_insight(request.question, results)
        
        # 8. Save Bot Response
        chat_history.add_message(
            role="bot", 
            content=insight, 
            metadata={
                "sql": sql_query,
                "data": results,
                "visualization_type": vis_type
            }
        )

        return QueryResponse(
            sql=sql_query,
            data=results,
            insight=insight,
            visualization_type=vis_type
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"CRITICAL ERROR: {str(e)}\n{tb}")
        raise HTTPException(status_code=500, detail=f"CRITICAL ERROR: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
