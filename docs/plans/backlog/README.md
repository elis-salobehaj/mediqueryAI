# Backlog Plans

**Last Updated**: 2026-01-22

Future ideas and enhancements not currently scheduled for active development.

---

## 💤 Future Work

### [Multi-Agent Reflexion Deep Dive](multi-agent-reflexion.md)
**Priority**: Medium | **Status**: Backlog

Advanced multi-agent architecture for complex queries:
- Specialized agents with focused responsibilities (Schema Navigator, SQL Writer, Critic)
- Cross-model critique (e.g., Claude critiques Gemini's SQL)
- Explicit state machine with conditional edges via LangGraph
- Optimized for handling 50+ table schemas with intricate joins
- Target use case: Complex oil & gas KPI datasets

**Dependencies**: Requires completion of [LangGraph Refactor](../active/langgraph-refactor.md)

---

## 📋 When to Promote from Backlog

Move a plan to `../active/` when:
1. Dependencies are resolved
2. Resources are available
3. Business priority increases
4. Technical prerequisites are met

**Process**:
1. Move file from `backlog/` to `active/`
2. Update frontmatter: `status: active`
3. Add to `docs/INDEX.md` active plans table
4. Update `docs/plans/active/README.md`
