from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env from project root (one level up from backend/)
# MUST BE DONE BEFORE IMPORTING SERVICES
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from contextlib import asynccontextmanager
import asyncio

from services.database import db_service
# Duplicate import removed
from services.llm_agent import llm_agent
from services.auth_service import auth_service

# Auth Deps
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, status
from datetime import timedelta
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

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

# Models
class QueryRequest(BaseModel):
    question: str
    model_id: str = "gemma-3-27b-it" # Default to High Quota model
    fast_mode: bool = False  # Skip plan construction for simple queries
    multi_agent: bool = False  # Use LangGraph multi-agent workflow for complex queries

class QueryResponse(BaseModel):
    sql: str
    data: dict
    insight: str
    visualization_type: str = "table" # 'bar', 'pie', 'line', 'scatter', 'map', 'table'
    error: str | None = None
    meta: dict | None = None
    attempts: int = 1  # Number of SQL generation attempts
    reflections: list[str] = []  # Self-critiques from failed attempts
    query_plan: str | None = None  # Natural language query plan
    agent_mode: str = "single"  # "single" or "multi"
    agents_used: list[str] | None = None  # e.g., ["schema_navigator", "sql_writer", "critic"]

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserCreate(User):
    password: str

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
        ALGORITHM = "HS256"
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
             raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_dict = auth_service.get_user(username)
    if user_dict is None:
        raise credentials_exception
    return user_dict

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

@app.get("/config/models")
async def get_models():
    """Returns the list of available LLM models."""
    return llm_agent.get_available_models()

from services.chat_history import chat_history

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    from datetime import datetime
    return {
        "status": "healthy",
        "service": "mediquery-ai-backend",
        "timestamp": datetime.now().isoformat(),
        "tables": db_service.get_schema().count("Table:")
    }

# --- Auth Routes ---
@app.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = auth_service.get_user(form_data.username)
    if not user_dict or not auth_service.verify_password(form_data.password, user_dict['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": user_dict['username']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/register", response_model=Token)
async def register_user(user: UserCreate):
    success = auth_service.create_user(user.username, user.password, user.full_name, user.email)
    if not success:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Auto login
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/guest", response_model=Token)
async def login_guest():
    """Creates a guest account and returns a token."""
    guest_username = auth_service.create_guest_user()
    access_token = auth_service.create_access_token(data={"sub": guest_username}, expires_delta=timedelta(hours=24))
    return {"access_token": access_token, "token_type": "bearer"}

# --- Protected Routes ---

@app.get("/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    """Returns recent chat messages."""
    messages = chat_history.get_recent_messages()
    return {"messages": messages}

@app.post("/query", response_model=QueryResponse)
async def query_data(request: QueryRequest = Body(...), current_user: dict = Depends(get_current_user)):
    try:
        # 1. Save User Message (Include Username)
        chat_history.add_message(role="user", content=request.question, metadata={"user": current_user['username']})

        # 2. Ensure configured
        if not llm_agent.api_key:
             api_key = os.getenv("GEMINI_API_KEY")
             if api_key and "YOUR_API_KEY" not in api_key:
                 llm_agent.configure(api_key)
             else:
                raise HTTPException(status_code=500, detail="Backend configuration error: API Key missing.")

        # 3. Get Schema
        schema = db_service.get_schema()

        # 4. Set Model
        if request.model_id:
            llm_agent.set_model(request.model_id)

        # Get recent history for context (last 5 messages)
        recent_history = chat_history.get_recent_messages(hours=24)
        
        # 5. HYBRID ROUTING: Multi-Agent vs Single-Agent
        if request.multi_agent:
            # Use LangGraph multi-agent workflow for complex queries
            logger.info(f"Routing to multi-agent workflow for user {current_user['username']}")
            
            try:
                from services.langgraph_agent import MultiAgentSQLGenerator
                
                multi_agent = MultiAgentSQLGenerator(
                    database_service=db_service,
                    llm_agent=llm_agent
                )
                
                multi_result = await multi_agent.ainvoke(
                    query=request.question,
                    username=current_user['username']
                )
                
                # Extract results from multi-agent workflow
                sql_query = multi_result.get("sql")
                results = multi_result.get("data")
                retry_error = multi_result.get("error")
                attempts = multi_result.get("attempts", 1)
                reflections = multi_result.get("reflections", [])
                query_plan = multi_result.get("query_plan")  # Multi-agent may not have query_plan
                agent_mode = "multi"
                agents_used = multi_result.get("agents_used", [])
                thoughts = multi_result.get("thoughts", [])
                
            except Exception as e:
                logger.error(f"Multi-agent workflow failed: {e}", exc_info=True)
                # Fallback to single-agent
                logger.info("Falling back to single-agent workflow")
                request.multi_agent = False
                retry_result = llm_agent.generate_sql_with_retry(
                    user_query=request.question,
                    schema_str=schema,
                    db_service=db_service,
                    history=recent_history,
                    fast_mode=request.fast_mode,
                    max_retries=3,
                    timeout_seconds=60
                )
                sql_query = retry_result.get("sql")
                results = None
                retry_error = retry_result.get("error")
                attempts = retry_result.get("attempts", 1)
                reflections = retry_result.get("reflections", [])
                agent_mode = "single"
                agents_used = None
                thoughts = llm_agent.last_thoughts
                query_plan = retry_result.get("query_plan")
        else:
            # Use existing single-agent reflexion loop
            retry_result = llm_agent.generate_sql_with_retry(
                user_query=request.question,
                schema_str=schema,
                db_service=db_service,
                history=recent_history,
                fast_mode=request.fast_mode,
                max_retries=3,
                timeout_seconds=60
            )
            sql_query = retry_result.get("sql")
            results = None
            retry_error = retry_result.get("error")
            attempts = retry_result.get("attempts", 1)
            reflections = retry_result.get("reflections", [])
            query_plan = retry_result.get("query_plan")
            agent_mode = "single"
            agents_used = None
            thoughts = llm_agent.last_thoughts
        
        # Handle retry failures (common for both paths)
        if (request.multi_agent and retry_error) or (not request.multi_agent and not retry_result.get("success")) or not sql_query:
            error_msg = retry_error or "Failed to generate valid SQL query"
            chat_history.add_message(role="bot", content=f"Query generation failed: {error_msg}")
            return QueryResponse(
                sql=sql_query or "",
                data={"row_count": 0, "columns": [], "data": []},
                insight=f"I attempted to generate a query {attempts} time(s) but encountered issues: {error_msg}",
                error=error_msg,
                visualization_type="table",
                attempts=attempts,
                reflections=reflections,
                query_plan=query_plan,
                agent_mode=agent_mode,
                agents_used=agents_used,
                meta={
                    "thoughts": thoughts,
                    "row_count": 0
                }
            )
        
        # Handle special SQL responses (RATE_LIMIT, etc.)
        if sql_query == "RATE_LIMIT":
            chat_history.add_message(role="bot", content="Google API Rate Limit Exceeded. Please try again in a minute.")
            return QueryResponse(
                sql="",
                data={"row_count": 0, "columns": [], "data": []},
                insight="**Rate Limit Exceeded**: The Google Gemini API is temporarily blocking requests due to high traffic/quota. Please wait 1-2 minutes and try again, or switch to a local model.",
                error="Rate Limit Exceeded",
                visualization_type="table",
                attempts=attempts,
                reflections=reflections,
                query_plan=query_plan,
                agent_mode=agent_mode,
                agents_used=agents_used
            )

        if sql_query == "INVALID_KEY":
             chat_history.add_message(role="bot", content="Google API Key is invalid.")
             return QueryResponse(
                sql="",
                data={"row_count": 0, "columns": [], "data": []},
                insight="**Configuration Error**: The Google Gemini API Key appears to be invalid or expired. Please check your `.env` file.",
                error="Invalid API Key",
                visualization_type="table",
                attempts=attempts,
                reflections=reflections,
                query_plan=query_plan,
                agent_mode=agent_mode,
                agents_used=agents_used
             )
        
        if sql_query and sql_query.startswith("API_ERROR"):
             chat_history.add_message(role="bot", content="External API Error.")
             return QueryResponse(
                sql="",
                data={"row_count": 0, "columns": [], "data": []},
                insight=f"**API Error**: {sql_query}",
                error=sql_query,
                visualization_type="table",
                attempts=attempts,
                reflections=reflections,
                query_plan=query_plan,
                agent_mode=agent_mode,
                agents_used=agents_used
             )

        if not sql_query or sql_query == "NO_MATCH":
            chat_history.add_message(role="bot", content="I couldn't find relevant data.")
            return QueryResponse(
                sql="",
                data={"row_count": 0, "columns": [], "data": []}, 
                insight="I'm sorry, I couldn't find relevant data in the database to answer your question. Please try asking about patients, visits, or billing.",
                visualization_type="table",
                attempts=attempts,
                reflections=reflections,
                query_plan=query_plan,
                agent_mode=agent_mode,
                agents_used=agents_used
            )

        # 6. Execute SQL (validation already done in retry loop or multi-agent workflow)
        if not results:
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
                    visualization_type="table",
                    attempts=attempts,
                    reflections=reflections,
                    query_plan=query_plan,
                    agent_mode=agent_mode,
                    agents_used=agents_used
                )

        # 7. Determine Visualization Type
        vis_type = llm_agent.determine_visualization(request.question, results)

        # 8. Generate Insight
        insight = llm_agent.generate_insight(request.question, results, history=recent_history)
        
        # 9. Save Bot Response
        chat_history.add_message(
            role="bot", 
            content=insight, 
            metadata={
                "sql": sql_query,
                "data": results,
                "visualization_type": vis_type,
                "attempts": attempts,
                "query_plan": query_plan
            }
        )

        return QueryResponse(
            sql=sql_query,
            data=results,
            insight=insight,
            visualization_type=vis_type,
            attempts=attempts,
            reflections=reflections,
            query_plan=query_plan,
            agent_mode=agent_mode,
            agents_used=agents_used,
            meta={
                "thoughts": thoughts,
                "row_count": results.get('row_count', 0)
            }
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"CRITICAL ERROR: {str(e)}\n{tb}")
        raise HTTPException(status_code=500, detail=f"CRITICAL ERROR: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
