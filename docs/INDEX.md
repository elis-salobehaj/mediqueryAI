# MediqueryAI Documentation Index

**For AI Agents**: Start here to understand current work and context.

**🤖 Agent Maintenance Instructions**: 
- When completing a task from a plan, check off the item in the plan's frontmatter `completion` list
- Update `date_updated` in the plan frontmatter
- Update this INDEX.md file to reflect current status
- When a plan is fully complete, move it from `plans/active/` to `plans/implemented/` and update status in this index

---

## 🔥 Active Plans (Priority Reading)

| Plan | Status | Priority | Last Updated | Progress | Related Files |
|------|--------|----------|--------------|----------|---------------|
| [Frontend UI Overhaul](plans/active/frontend_ui_overhaul.md) | In Progress | High | 2026-01-24 | 4/7 phases ✅ | `frontend/src/index.css`, `frontend/src/components/*` |
| [LangGraph Refactor](plans/active/langgraph-refactor.md) | In Progress | High | 2026-01-22 | 2/5 steps ✅ | `backend/services/langgraph_agent.py` |

**Current Focus**: 
- 🔄 **Frontend UI Overhaul**: Migrating to Tailwind v4, OKLCH colors, Container Queries
- ✅ Pydantic Settings v2 configuration complete
- ✅ Dependency isolation complete (google-genai removed from Bedrock mode)

**Quick Context**: 2026 Frontend Architecture Overhaul - CSS-first theming with OKLCH colors, container queries for responsive components, and zero-JS-runtime theme switching.

---

## 📊 Current Reports

*No active implementation reports. Recent work documented in plan frontmatter.*

---

## 📚 Implementation Guides (Always Relevant)

**Development:**
- [Testing Guide](guides/TESTING_GUIDE.md) - Unit, integration, E2E test patterns
- [Requirements Guide](guides/REQUIREMENTS_GUIDE.md) - Modular dependency management (base, bedrock, local, full)
- [Local Model Setup](guides/LOCAL_MODEL_SETUP.md) - Ollama configuration for local LLM development

**Deployment:**
- [Docker Deployment](guides/DOCKER_DEPLOYMENT.md) - Container setup and configuration

**Features:**
- [Chat History Auto-Deletion](guides/CHAT_HISTORY_AUTO_DELETION.md) - User privacy and data retention

---

## ✅ Recently Completed

| Plan | Completed | Summary |
|------|-----------|---------|
| [MediqueryAI Features](plans/implemented/mediqueryai-features.md) | 2026-01-20 | CSV export + SQL Reflexion loop with retry logic |

---

## 🗂️ Archive Reference

<details>
<summary>Future Plans (Backlog) - Expand if needed</summary>

- [Multi-Agent Reflexion Deep Dive](plans/backlog/multi-agent-reflexion.md) - Advanced multi-agent architecture for complex oil & gas KPI queries

</details>

<details>
<summary>Historical Reports (2026) - Expand if needed</summary>

- [Dependency Analysis Report](reports/archive/2026/DEPENDENCY_ANALYSIS_REPORT.md) - Modular requirements structure
- [Multi-Agent Fix Summary](reports/archive/2026/MULTI_AGENT_FIX_SUMMARY.md) - Query timeout and retry fixes
- [Phase 1 Implementation Summary](reports/archive/2026/PHASE1_IMPLEMENTATION_SUMMARY.md) - CSV export + Reflexion loop
- [SQL Cleaning Fix Report](reports/archive/2026/SQL_CLEANING_FIX_REPORT.md) - SQL sanitization improvements

</details>

---

## 🎯 For AI Coding Agents

**When asked to implement a feature:**
1. Check `docs/plans/active/` for relevant plan
2. Read linked files in frontmatter `related_files`
3. Check `docs/reports/current/` for context on recent changes
4. Reference `docs/guides/` for coding standards

**When generating reports:**
- Save to `docs/reports/current/` while work is ongoing
- Include frontmatter with status and related_files
- Link back to the original plan

**When a plan is complete:**
- Move from `plans/active/` to `plans/implemented/`
- Update status in frontmatter to `implemented`
- Archive related reports to `reports/archive/{year}/`

---

## Project Architecture

```
mediqueryAI/
├── backend/          # FastAPI + LangGraph
├── frontend/         # React + TypeScript
└── docs/             # You are here
```

**Tech Stack**: Python 3.12, FastAPI, LangGraph, React 19, TypeScript, Tailwind v4, MySQL
**Key Services**: 
- `backend/services/langgraph_agent.py` - Multi-agent SQL workflow
- `backend/services/llm_agent.py` - LLM interaction layer
- `backend/config.py` - Pydantic Settings v2 configuration
