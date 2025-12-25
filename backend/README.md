# MediQuery AI - Backend

The intelligent core of the MediQuery AI system. Built with FastAPI and Python, it orchestrates the interaction between the user, the LLM (Ollama/Gemini), and the SQLite database.

## 🧠 Smart Agent Logic

The backend features a sophisticated **LLM Agent** (`services/llm_agent.py`) designed to translate natural language into optimized SQL. Key capabilities include:

- **Ambiguous Query Resolving**: Intelligently searches both `patients.chronic_condition` AND `visits.diagnosis` (using LEFT JOINs) when a user asks about an illness like "diabetes" without specifying the context.
- **Smart Schema Inference**:
  - **Demographics**: Queries ONLY the `patients` table for faster, cleaner results (e.g., "count by state").
  - **Financials**: Correctly navigates the `billing` -> `visits` -> `patients` join path.
- **Typo Tolerance**: Fuzzy matching instructions for the LLM to handle user input errors.
- **Context Awareness**: Maintains chat history to handle follow-up questions ("show me *their* details").

## 🛠️ Tech Stack

- **FastAPI**: High-performance Async IO web framework.
- **LlamaIndex**: For semantic retrieval (optional RAG capabilities).
- **SQLite**: Local relational database.
- **Ollama / Google Gemini**: Hybrid LLM support.
- **Pandas**: For data formatting and CSV export.

## 🧪 Testing

We use **Pytest** for backend logic tests.

### Dockerized Testing (Recommended)
Run the full suite in an isolated container:
```powershell
# Windows
..\run-tests.ps1

# Linux/Mac
../run-tests.sh
```

### Manual Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```
