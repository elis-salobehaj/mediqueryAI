# Active Plans

**Last Updated**: 2026-01-22

## 🔥 In Progress

### [LangGraph Refactor](langgraph-refactor.md)
**Priority**: High | **Status**: In Progress (2/5 steps complete)  
**Assignee**: TBD | **Target**: 2026-01-25

Refactoring multi-agent workflow to use LangGraph for:
- ✅ AWS Bedrock integration with Bearer Token auth (Claude 4.5 models)
- ✅ Modular requirements and dependencies added
- 🔄 Better state management with conditional routing
- 🔄 SQL deduplication to prevent infinite retries
- 🔄 Early timeout checks in agent nodes

**Related Files**: `backend/services/langgraph_agent.py`, `backend/main.py`, `backend/requirements.txt`

---

## 📋 Instructions for AI Agents

**When completing a task from a plan**:
1. ✅ Check off the item in the plan's frontmatter `completion` list
2. 📅 Update `date_updated` in the plan frontmatter
3. 📝 Update progress in this README
4. 🔄 Update `docs/INDEX.md` to reflect current status

**Example edit to plan frontmatter**:
```yaml
completion:
  - [x] Step 1 - Configure Environment Variables ✅
  - [x] Step 2 - Add AWS Bedrock integration ✅
  - [ ] Step 3 - Fix routing logic
```

**When complete**:
1. Move plan to `../implemented/`
2. Update frontmatter: `status: implemented`, add `date_completed`
3. Create final report in `docs/reports/archive/{year}/`
4. Update `docs/INDEX.md`
