# GitHub Copilot Instructions for MediqueryAI

## Documentation Structure

**Always start with**: [`docs/INDEX.md`](../docs/INDEX.md) for current work context

**When implementing features**:
1. Check `docs/plans/active/` for the implementation plan
2. Read YAML frontmatter for related files
3. Follow patterns in existing code
4. **REQUIRED**: Update plan progress as you work (see maintenance rules below)

**When creating reports**:
- Use frontmatter with status, date, related_files
- Save to `docs/reports/current/` during work
- Move to `docs/reports/archive/{year}/` when complete

---

## 🔄 Documentation Maintenance Rules

**CRITICAL: After completing ANY task from a plan, you MUST**:

1. **Update the plan file** (`docs/plans/active/*.md`):
   ```yaml
   # In frontmatter completion list:
   - [x] Step 2 - Add AWS Bedrock integration ✅
   date_updated: 2026-01-22  # Update this
   ```

2. **Update `docs/INDEX.md`**:
   ```markdown
   | Plan | Status | Progress | Last Updated |
   |------|--------|----------|--------------|
   | LangGraph Refactor | In Progress | 3/5 steps ✅ | 2026-01-22 |
   ```

3. **Update `docs/plans/active/README.md`**:
   - Change progress indicator
   - Update "Last Updated" date
   - Add completed checkmarks

4. **When plan is 100% complete**:
   ```bash
   # Move plan to implemented
   git mv docs/plans/active/plan-name.md docs/plans/implemented/
   
   # Update frontmatter
   status: implemented
   date_completed: 2026-01-22
   
   # Update INDEX.md to move from Active to Completed table
   ```

**Example workflow**:
```
[You complete Step 2 of LangGraph refactor]
→ Update langgraph-refactor.md frontmatter (check off Step 2, update date)
→ Update docs/INDEX.md (change "1/5 steps" to "2/5 steps")
→ Update docs/plans/active/README.md (add ✅ to Step 2)
→ Commit changes with plan updates
```

---

## Code Conventions

**Python Backend** (`backend/`):
- Type hints required
- Docstrings for public methods
- Use `logger` not `print()`
- Async-first for I/O operations

**React Frontend** (`frontend/src/`):
- TypeScript strict mode
- Functional components with hooks
- Props interfaces required
- Use Tailwind for styling

**Testing**:
- Unit tests in `backend/tests/`
- E2E tests in `frontend/tests/`
- See [`docs/guides/TESTING_GUIDE.md`](../docs/guides/TESTING_GUIDE.md)

## Active Work Context

**Current Sprint**: LangGraph multi-agent refactor + AWS Bedrock integration
**Blocked**: Bedrock integration (waiting for API key)
**Priority Files**:
- `backend/services/langgraph_agent.py`
- `backend/main.py`

## Ignore for Code Suggestions

- `docs/plans/backlog/` - Future work, not current
- `docs/reports/archive/` - Historical reference only
- `*.prompt.md` files - Prompt templates for other agents

## When Confused

1. Read [`docs/INDEX.md`](../docs/INDEX.md)
2. Check plan frontmatter for `related_files`
3. Look at recent commits: `git log --oneline -10`
