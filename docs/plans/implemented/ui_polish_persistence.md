---
status: active
priority: high
date_created: 2026-01-23
date_updated: 2026-01-24
related_files:
  - backend/services/chat_history.py
  - frontend/src/App.tsx
  - frontend/src/components/Chat/ChatInterface.tsx
  - frontend/src/components/Chat/PlotlyVisualizer.tsx
  - frontend/src/index.css
  - AGENTS.md
  - backend/config.py
  - backend/main.py
  - backend/services/llm_agent.py
completion:
  - [x] Step 0 - Documentation Update (AGENTS.md)
  - [x] Step 1 - Infrastructure Upgrades (React 19, Tailwind v4)
  - [ ] Step 2 - Backend Persistence Fix (Re-verify)
  - [ ] Step 3 - Frontend Persistence (Re-verify)
  - [ ] Step 4 - Frontend Theming & Alignment (Re-verify)
  - [ ] Step 5 - Configuration Refactor (Pydantic & Isolation)
  - [ ] Step 6 - Dependency Cleanup
---

# Plan: UI Polish, Persistence & Config Refactor

**Date**: January 24, 2026
**Status**: Completed
**Goal**: Universal Persistence, Abyss Theme, Perfect Alignment, and Robust Configuration (Pydantic/Dependency Isolation).

## Problem Statement
The application has issues with:
- **Persistence**: Thinking process is not consistently reliably persisted/restored.
- **Alignment**: Visual misalignments between Input Bar and Chat.
- **Architecture**: Backend relies on scattered `os.getenv` calls and has coupled dependencies (`google-genai` required even for Bedrock).
- **Stability**: Missing dependencies cause crashes instead of handled errors.

## Phases

### Step 0: Documentation
**Target**: `AGENTS.md`
- [x] Update "Tech Stack" to specify **Python (managed by uv)** and **React 19 (managed by pnpm)**.

### Step 1: Infrastructure Upgrades
**Target**: `frontend/package.json`, `frontend/index.css`
- [x] Upgrade to React 19 and Tailwind v4.

### Step 2: Backend Persistence (Correction)
**Target**: `backend/services/chat_history.py`, `backend/main.py`
- Ensure `add_message` persists the `metadata` (containing `thoughts`) to SQLite/JSON.
- **Fix**: Ensure `metadata` is passed correctly in ALL `add_message` calls, especially inside error handlers in `main.py`.

### Step 3: Frontend Persistence (Correction)
**Target**: `frontend/src/App.tsx`
- Ensure `fetchMessages` correctly maps `metadata.thoughts`.
- Verify the "Show thinking" toggle appears and works after page refresh.

### Step 4: Theming & Alignment (Correction)
**Target**: `frontend/src/index.css`, `PlotlyVisualizer.tsx`, `ChatInterface.tsx`
- **Alignment**:
    - Use `scrollbar-gutter: stable` to prevent layout shift.
    - Ensure `max-w-4xl` is consistent between Input and Chat.
- **Theming**:
    - Ensure Plotly charts update *instantly* on theme toggle (use `key={theme}`).

### Step 5: Configuration Refactor & Isolation
**Target**: `backend/config.py`, `backend/main.py`, `backend/services/llm_agent.py`
- **Config**: Create `backend/config.py` using `pydantic-settings`. Define strict schema for env vars.
- **Refactor**: Replace ALL `os.getenv` calls with `settings` object.
- **Isolation**: In `llm_agent.py`, logic MUST respect `USE_BEDROCK`.
    - IF `USE_BEDROCK=true`, DO NOT import/init `google-genai` or check for `GEMINI_API_KEY`.

### Step 6: Dependency Cleanup
**Target**: `backend/requirements-bedrock.txt`
- Remove `google-genai` from `requirements-bedrock.txt`.
- Ensure `pydantic-settings` is in `requirements.txt`.

## Verification Checklist
### Automated
- [ ] `docker compose up --build backend` succeeds without `google-genai` in Bedrock mode.
- [ ] Persistence probe passes (thoughts are saved).
- [ ] `backend/tests/test_config.py` passes (Settings load correctly).

### Browser & UI Verification
- [ ] **Frontend Rebuild**: `docker compose up --build frontend` (Ensure clean build).
- **Browser Scenario**: "find patients with flu by state"
- [ ] **Alignment**: Input Bar left edge == Chat Icon left edge.
- [ ] **Persistence**: Refresh page -> "Thinking" toggle persists.
- [ ] **Backend Response**: Returns valid data/SQL (no 500 Network Error).
- [ ] **Theming**: Toggle Light/Dark -> Chart updates instantly.
