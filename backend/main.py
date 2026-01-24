from pathlib import Path
import os
from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, status
from datetime import timedelta
from jose import JWTError, jwt

# Config
from config import settings

from services.database import db_service
from services.llm_agent import llm_agent
from services.auth_service import auth_service
from services.chat_history import chat_history

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Configure Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ],
    force=True
)
logger = logging.getLogger(__name__)

# --- Models ---

class QueryRequest(BaseModel):
    question: str
    thread_id: str | None = None
    model_id: str = "gemma-3-27b-it" 
    fast_mode: bool = False
    multi_agent: bool = False

class QueryResponse(BaseModel):
    sql: str
    data: dict
    insight: str
    visualization_type: str = "table"
    error: str | None = None
    meta: dict | None = None
    attempts: int = 1
    reflections: list[str] = []
    query_plan: str | None = None
    agent_mode: str = "single"
    agents_used: list[str] | None = None

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

class ThreadCreate(BaseModel):
    title: str = "New Chat"

class ThreadUpdate(BaseModel):
    title: str | None = None
    pinned: bool | None = None

# --- Helpers ---

import math
def clean_nans(obj):
    """Recursively replace NaN/Infinity with None for JSON compliance."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    elif isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nans(v) for v in obj]
    return obj

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
             raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_dict = auth_service.get_user(username)
    if user_dict is None:
        raise credentials_exception
    return user_dict

# --- App Lifecycle ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load data
    logger.info("Initializing application and loading data...")
    try:
        llm_agent.configure(settings) 
    except Exception as e:
        logger.error(f"Failed to configure agent on startup: {e}")
    
    # Prune history on startup
    try:
        chat_history.prune_old_messages(settings.chat_history_retention_hours)
        logger.info("Chat history pruned on startup.")
    except Exception as e:
        logger.warning(f"Failed to prune history: {e}")
    
    # Start background task to prune history periodically (every hour)
    async def prune_history_periodically():
        """Background task to prune expired chat history every hour."""
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
            try:
                chat_history.prune_old_messages(settings.chat_history_retention_hours)
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

# --- Routes ---

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

@app.get("/config/models")
async def get_models():
    """Returns the list of available LLM models."""
    return llm_agent.get_available_models()

# Auth Routes
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

# Thread Routes
@app.get("/threads")
async def get_threads(current_user: dict = Depends(get_current_user)):
    """Returns list of threads for the current user."""
    threads = chat_history.get_user_threads(current_user['username'])
    return {"threads": clean_nans(threads)}

@app.post("/threads")
async def create_thread(thread: ThreadCreate, current_user: dict = Depends(get_current_user)):
    """Creates a new thread."""
    thread_id = chat_history.create_thread(current_user['username'], thread.title)
    return {"id": thread_id, "title": thread.title}

@app.get("/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str, current_user: dict = Depends(get_current_user)):
    """Returns messages for a specific thread."""
    messages = chat_history.get_thread_messages(thread_id)
    return {"messages": clean_nans(messages)}

@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str, current_user: dict = Depends(get_current_user)):
    """Deletes a thread."""
    chat_history.delete_thread(thread_id)
    return {"status": "success"}

@app.patch("/threads/{thread_id}")
async def update_thread(thread_id: str, update: ThreadUpdate, current_user: dict = Depends(get_current_user)):
    """Updates thread title or pinned status."""
    chat_history.update_thread(thread_id, title=update.title, pinned=update.pinned)
    return {"status": "success"}

# Query Route
@app.post("/query", response_model=QueryResponse)
async def query_data(request: QueryRequest = Body(...), current_user: dict = Depends(get_current_user)):
    try:
        # 1. Manage Thread
        thread_id = request.thread_id
        if not thread_id:
            initial_title = request.question[:30] + "..." if len(request.question) > 30 else request.question
            thread_id = chat_history.create_thread(current_user['username'], title=initial_title)
        
        # 2. Save User Message
        chat_history.add_message(thread_id, role="user", content=request.question, metadata={"user": current_user['username']})

        # 3. Ensure configured
        try:
            logger.info("Checking Agent Configuration...")
            # Re-configure with current settings in case of hot-reload or initial failure
            # configure() is robust and will handle if already configured or if keys missing
            llm_agent.configure(settings) 
            
            # Explicit check if we are in Gemini mode but missing key
            if not settings.use_bedrock and not settings.use_local_model:
                 if not settings.gemini_api_key or "YOUR_API_KEY" in settings.gemini_api_key:
                     raise ValueError("Gemini API Key missing or invalid in settings.")
                     
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Configuration Error: {error_msg}")
            chat_history.add_message(
                thread_id, 
                role="bot", 
                content=f"Configuration Error: {error_msg}",
                metadata={"thoughts": ["Error during configuration."], "thread_id": thread_id}
            )
            return QueryResponse(
                sql="", data={"row_count": 0, "columns": [], "data": []},
                insight=f"I cannot proceed because: {error_msg}",
                error=error_msg, visualization_type="table", attempts=0, 
                meta={"thoughts": ["Error during configuration."], "thread_id": thread_id}
            )

        # 4. Get Schema
        schema = db_service.get_schema()

        # 5. Set Model
        if request.model_id:
            llm_agent.set_model(request.model_id)

        # Get recent history for context
        thread_messages = chat_history.get_thread_messages(thread_id)
        history_context = []
        for msg in thread_messages[-10:]:
             history_context.append({"role": msg['role'], "content": msg['text']})

        # 6. Logic Routing
        if request.multi_agent:
            logger.info(f"Routing to multi-agent workflow for user {current_user['username']}")
            try:
                from services.langgraph_agent import MultiAgentSQLGenerator
                multi_agent = MultiAgentSQLGenerator(database_service=db_service, llm_agent=llm_agent)
                multi_result = await multi_agent.ainvoke(query=request.question, username=current_user['username'])
                
                sql_query = multi_result.get("sql")
                results = multi_result.get("data")
                retry_error = multi_result.get("error")
                attempts = multi_result.get("attempts", 1)
                reflections = multi_result.get("reflections", [])
                query_plan = multi_result.get("query_plan")
                agent_mode = "multi"
                agents_used = multi_result.get("agents_used", [])
                thoughts = multi_result.get("thoughts", [])
            except Exception as e:
                logger.error(f"Multi-agent workflow failed: {e}", exc_info=True)
                request.multi_agent = False
                retry_result = llm_agent.generate_sql_with_retry(
                    user_query=request.question, schema_str=schema, db_service=db_service,
                    history=history_context, fast_mode=request.fast_mode, max_retries=3, timeout_seconds=60
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
            retry_result = llm_agent.generate_sql_with_retry(
                user_query=request.question, schema_str=schema, db_service=db_service,
                history=history_context, fast_mode=request.fast_mode, max_retries=3, timeout_seconds=60
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

        # Handle Failures
        if (request.multi_agent and retry_error) or (not request.multi_agent and not retry_result.get("success")) or not sql_query:
            error_msg = retry_error or "Failed to generate valid SQL query"
            chat_history.add_message(thread_id, role="bot", content=f"Query generation failed: {error_msg}")
            return QueryResponse(
                sql=sql_query or "", data={"row_count": 0, "columns": [], "data": []},
                insight=f"I attempted to generate a query {attempts} time(s) but encountered issues: {error_msg}",
                error=error_msg, visualization_type="table", attempts=attempts, reflections=reflections,
                query_plan=query_plan, agent_mode=agent_mode, agents_used=agents_used,
                meta={"thoughts": thoughts, "row_count": 0, "thread_id": thread_id}
            )

        # Handle Rate Limit
        if sql_query == "RATE_LIMIT":
            chat_history.add_message(thread_id, role="bot", content="Google API Rate Limit Exceeded.")
            return QueryResponse(
                sql="", data={"row_count": 0, "columns": [], "data": []},
                insight="**Rate Limit Exceeded**: Please wait 1-2 minutes.",
                error="Rate Limit Exceeded", visualization_type="table", attempts=attempts, reflections=reflections,
                query_plan=query_plan, agent_mode=agent_mode, agents_used=agents_used, meta={"thread_id": thread_id}
            )

        # Execute SQL
        if not results:
            try:
                results = db_service.execute_query(sql_query)
                if not results: results = {"row_count": 0, "columns": [], "data": []}
            except Exception as e:
                logger.error(f"SQL Execution Error: {e}")
                chat_history.add_message(thread_id, role="bot", content=f"Database Error: {str(e)}")
                return QueryResponse(
                    sql=sql_query, data={"row_count": 0, "columns": [], "data": []},
                    insight=f"I generated a query but it failed to execute. Error: {str(e)}",
                    error=str(e), visualization_type="table", attempts=attempts, reflections=reflections,
                    query_plan=query_plan, agent_mode=agent_mode, agents_used=agents_used, meta={"thread_id": thread_id}
                )

        # Generate Insight
        vis_type = llm_agent.determine_visualization(request.question, results)
        insight = llm_agent.generate_insight(request.question, results, history=history_context)
        
        chat_history.add_message(
            thread_id, role="bot", content=insight, 
            metadata={
                "sql": sql_query, "data": results, "visualization_type": vis_type,
                "attempts": attempts, "query_plan": query_plan,
                "thoughts": thoughts # Save thinking process for persistence
            }
        )

        return QueryResponse(
            sql=sql_query, data=clean_nans(results), insight=insight, visualization_type=vis_type,
            attempts=attempts, reflections=reflections, query_plan=query_plan,
            agent_mode=agent_mode, agents_used=agents_used,
            meta=clean_nans({"thoughts": thoughts, "row_count": results.get('row_count', 0), "thread_id": thread_id})
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"CRITICAL ERROR: {str(e)}\n{tb}")
        raise HTTPException(status_code=500, detail=f"CRITICAL ERROR: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
