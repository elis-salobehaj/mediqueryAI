# AI Agent Instructions for MediqueryAI

## Documentation Structure

**Always start with**: [`docs/INDEX.md`](./docs/INDEX.md) for current work context.

**When implementing features**:
1. Check `docs/plans/active/` for the implementation plan.
2. Read YAML frontmatter for related files.
3. Follow patterns in existing code.
4. **REQUIRED**: Update plan progress as you work (see maintenance rules below).

**When creating reports**:
- Use frontmatter with status, date, related_files.
- Save to `docs/reports/current/` during work.
- Move to `docs/reports/archive/{year}/` when complete.

---

## 🧬 Tech Stack & Architecture

### Backend (Python 3.12)
- **Package Manager**: `uv`
- **Framework**: FastAPI (async-first)
- **AI Orchestration**: LangGraph (multi-agent workflows)
- **Database**: MySQL + SQLAlchemy
- **Configuration**: Pydantic Settings v2 (see Configuration section)

### Frontend (2026 Standards)
- **Framework**: React 19 + TypeScript (strict mode)
- **Package Manager**: `pnpm`
- **Styling**: Tailwind CSS v4 with `@theme` directive
- **Color Space**: OKLCH (perceptually uniform)
- **Responsiveness**: Container Queries (`@container`)
- **Testing**: Playwright for E2E

---

## 🎨 Frontend Architecture (2026)

### CSS-First Theming
All design tokens must be in native CSS, not JavaScript:
```css
@theme {
  --color-brand: oklch(65% 0.25 260);
  --color-surface: oklch(98% 0.01 260);
}

[data-theme="dark"] {
  --color-surface: oklch(15% 0.05 260);
}
```

### Container Queries
Components adapt to their **container width**, not screen width:
```html
<div class="@container">
  <div class="flex flex-col @min-w-md:flex-row">
    <!-- Stacks vertically when narrow, horizontal when wide -->
  </div>
</div>
```

### Theme Switching (Zero-JS Runtime)
```javascript
const toggleTheme = (themeName) => {
  document.documentElement.setAttribute('data-theme', themeName);
  localStorage.setItem('theme', themeName);
};
```

### Performance Goals
| Metric | Target |
|--------|--------|
| CSS Bundle | < 10KB |
| Theme Switch INP | < 50ms |
| CLS on Toggle | 0 |

---

## ⚙️ Backend Configuration (Pydantic v2)

### Configuration Pattern
All backend configuration MUST use `pydantic-settings`:

```python
# backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Required
    gemini_api_key: str | None = None
    
    # Feature Flags
    use_bedrock: bool = False
    use_local_model: bool = False
    
    # AWS (Optional)
    aws_bedrock_region: str = "us-west-2"
    bedrock_sql_writer_model: str = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

settings = Settings()
```

### Usage Rules
1. **NEVER use `os.getenv()` directly** - always use `settings.attribute`
2. **Dependency Isolation**: Code paths must respect feature flags
   ```python
   if settings.use_bedrock:
       # Only import/init Bedrock clients here
   elif settings.use_local_model:
       # Only import/init Ollama here
   else:
       # Default to Gemini
   ```
3. **Graceful Fallbacks**: Missing optional keys should have sensible defaults

---

## 🛠️ Essential Commands

### Environment Setup
```bash
# Backend
uv sync

# Frontend
pnpm install
```

### Development
```bash
# API Server (port 8000)
uv run dev

# UI Server (port 3000)
pnpm dev
```

### Testing
```bash
# Backend tests
uv run pytest

# E2E tests
pnpm playwright test

# Debug mode
pnpm playwright test --ui
```

### Linting
```bash
uv run ruff check .
pnpm lint
```

---

## 🔄 Documentation Maintenance Rules

**CRITICAL: After completing ANY task from a plan, you MUST**:

1. **Update the plan file** (`docs/plans/active/*.md`):
   ```yaml
   # In frontmatter completion list:
   - [x] Phase 1 - Global Style Definition ✅
   date_updated: 2026-01-24
   ```

2. **Update `docs/INDEX.md`**:
   ```markdown
   | Plan | Status | Progress | Last Updated |
   |------|--------|----------|--------------|
   | Frontend UI Overhaul | In Progress | 1/6 phases ✅ | 2026-01-24 |
   ```

3. **When plan is 100% complete**:
   ```bash
   git mv docs/plans/active/plan-name.md docs/plans/implemented/
   ```

---

## Code Conventions

### Python Backend
- Type hints required
- Docstrings for public methods
- Use `logger` not `print()`
- Async-first for I/O operations
- Use `settings` object for configuration

### React Frontend
- TypeScript strict mode
- Functional components with hooks
- Props interfaces required
- Use CSS variables for theming (no hardcoded colors)
- Use Container Queries for responsiveness

### Testing
- Unit tests in `backend/tests/`
- E2E tests in `frontend/tests/`
- See [`docs/guides/TESTING_GUIDE.md`](./docs/guides/TESTING_GUIDE.md)

---

## Active Work Context

**Current Sprint**: Frontend UI Overhaul (2026 Standards)
**Active Plan**: `docs/plans/active/frontend_ui_overhaul.md`

**Priority Files**:
- `frontend/src/index.css` (OKLCH migration)
- `frontend/src/components/Layout/*`
- `frontend/src/components/Chat/*`

## Ignore for Code Suggestions

- `docs/plans/backlog/` - Future work, not current
- `docs/reports/archive/` - Historical reference only
- `*.prompt.md` files - Prompt templates for other agents

## When Confused

1. Read [`docs/INDEX.md`](./docs/INDEX.md)
2. Check plan frontmatter for `related_files`
3. Look at recent commits: `git log --oneline -10`
