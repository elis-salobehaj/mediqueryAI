# MediQuery AI - Backend

The intelligent core of the MediQuery AI system. Built with FastAPI and Python, it orchestrates the interaction between the user, the LLM (Ollama/Gemini), and the SQLite database.

## 🧠 Smart Agent Logic

The backend features a sophisticated **LLM Agent** (`services/llm_agent.py`) designed to translate natural language into optimized SQL. Key capabilities include:

### Core Intelligence
- **Ambiguous Query Resolving**: Intelligently searches both `patients.chronic_condition` AND `visits.diagnosis` (using LEFT JOINs) when a user asks about an illness like "diabetes" without specifying the context.
- **Smart Schema Inference**:
  - **Demographics**: Queries ONLY the `patients` table for faster, cleaner results (e.g., "count by state").
  - **Financials**: Correctly navigates the `billing` -> `visits` -> `patients` join path.
- **Typo Tolerance**: Fuzzy matching instructions for the LLM to handle user input errors.
- **Context Awareness**: Maintains chat history to handle follow-up questions ("show me *their* details").

### Phase 1 Features 🆕
- **SQL Reflexion Loop**: Self-correcting SQL generation with up to 3 retry attempts
  - Validates SQL with dry-run EXPLAIN queries
  - AI-powered error analysis and reflection
  - 60-second timeout protection
- **Query Planning**: Generates natural language execution plans before SQL generation
- **Fast Mode**: Optional bypass of query planning for 60% faster responses
- **Robust Validation**: Handles trailing semicolons, row count checks, edge case warnings
- **Multi-Tenant Ready**: User-scoped caching infrastructure prepared

### Multi-Agent System 🌟
- **LangGraph StateGraph**: Orchestrates specialized agents for complex queries
- **Three Specialized Agents**:
  - **Schema Navigator** (`qwen2.5-coder:7b`): Selects relevant tables using semantic search
  - **SQL Writer** (`sqlcoder:7b`): Generates optimized SQL with context awareness
  - **Critic** (`llama3.1`): Cross-model validation for diverse perspective
- **Reflection Loop**: Automatic error analysis and retry with feedback
- **Ollama-First Architecture**: Defaults to local models, falls back to cloud
- **Environment Configuration**: Per-agent model selection via env vars
- **Hybrid Routing**: User toggle between single-agent and multi-agent modes

## 🛠️ Tech Stack

- **FastAPI**: High-performance Async IO web framework.
- **LlamaIndex**: For semantic retrieval (optional RAG capabilities).
- **SQLite**: Local relational database.
- **Ollama / Google Gemini**: Hybrid LLM support.
- **Pandas**: For data formatting and CSV export.

## 🧪 Testing

We use **Pytest** for backend unit tests with comprehensive Phase 1 coverage.

### Quick Test Commands
```bash
# Run all Phase 1 tests (15 tests)
docker exec mediquery-ai-backend python -m pytest /app/tests/test_phase1.py -v

# Run all backend tests
docker exec mediquery-ai-backend python -m pytest /app/tests/ -v

# Run specific test categories
docker exec mediquery-ai-backend python -m pytest /app/tests/test_auth.py -v
docker exec mediquery-ai-backend python -m pytest /app/tests/test_basic.py -v
```

### Test Coverage (37 total tests)
- **test_phase1.py** (15 tests): SQL validation, Reflexion loop, CSV export data structures, multi-tenant isolation
- **test_langgraph_agent.py** (8 tests): Multi-agent workflow, state management, agent coordination, hybrid routing
- **test_auth.py** (5 tests): JWT authentication and authorization
- **test_basic.py** (1 test): Database connectivity and core functionality
- **test_config.py** (2 tests): Model selection and configuration
- **test_context.py** (1 test): LLM agent history integration
- **test_model_switching.py** (1 test): Dynamic LLM selection
- **test_semantic.py** (2 tests): Semantic search and table retrieval
- **test_visualization.py** (1 test): Chart type selection logic
- **test_auto_deletion.py** (1 test): Chat history auto-deletion

### Dockerized Testing (Recommended)
Run tests in an isolated container:
```bash
# Linux/Mac
../run-ci.sh  # Includes backend unit tests

# Windows
..\run-ci.ps1
```

### Manual Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -v
```
