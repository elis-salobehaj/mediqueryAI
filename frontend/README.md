# MediQuery AI - Frontend

The futuristic interface for the MediQuery AI healthcare data agent. Built with React 19, Vite, and Tailwind CSS.

## 🌟 Key Features

- **Cyberpunk / Sci-Fi Aesthetic**: Dark mode glassmorphism UI with futuristic HUD design.
- **Explainable AI Interface**: 
  - Displays the agent's **"Thinking Process"** in a collapsible detail view.
  - Shows multi-agent workflow steps (Schema Navigator → SQL Writer → Critic).
  - Displays raw SQL generation and validation results.
  - Transparent error handling with reflection feedback.
- **Dynamic Visualization Engine**:
  - `PlotlyVisualizer.tsx` component automatically selects 1 of 60+ chart types based on data.
  - Interactive zooming, panning, and exporting.
  - Real-time chart type switching.
- **Dual-Mode Toggles**:
  - **Fast/Thinking**: Choose between quick responses (⚡) or detailed reasoning (🧠)
  - **Single/Multi-Agent**: Toggle between simple queries (🤖) or complex multi-agent workflow (🤖)
- **CSV Export**: Download query results with a single click.
- **Responsive Layout**: Works on desktop and large tablets.

## 🛠️ Technology Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite (Blazing fast HMR)
- **Styling**: Tailwind CSS + Custom CSS Variables
- **Charts**: `react-plotly.js`
- **Markdown**: `react-markdown` for streaming text rendering

## 🚀 Development Setup

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Run Development Server**:
   ```bash
   npm run dev
   ```
   Access at `http://localhost:3000`.

3. **Build for Production**:
   ```bash
   npm run build
   ```

## 📂 Project Structure

- `src/`
  - `main.tsx`: Application entry point.
  - `App.tsx`: Main layout wrapper and routing logic.
  - `index.css`: Global styles and Tailwind directives.
  - `components/`: Reusable UI components
    - `ChatBox.tsx`: The heart of the app. Handles user input, keeps chat history, and displays the **Thinking Process**.
    - `PlotlyVisualizer.tsx`: The brain of the visualization logic (60+ chart types).
    - `Configuration.tsx`: Settings panel for model selection (Local vs Cloud).
    - `Login.tsx`: User authentication interface.

## 🧪 Testing

We use **Playwright** for both Component and End-to-End testing.

### Component Tests (Fast - 10 tests)
```bash
# Run locally
npx playwright test

# Run in Docker (recommended for CI)
cd ..
./run-ci.sh  # Includes frontend component tests
```

**Test Coverage:**
- ChatBox component (user input, message rendering, toggles)
- Configuration component (model selection)
- Login component (authentication flows)
- PlotlyVisualizer component (chart rendering and switching)

### E2E Tests (Full Stack - 2 tests)
```bash
# Run locally (requires backend running)
npx playwright test -c playwright-e2e.config.ts

# Run in Docker (recommended - full stack)
cd ..
./run-e2e.sh  # Spins up backend + frontend + runs tests
```

**Test Coverage:**
- Guest login and authentication flow
- Configuration endpoint validation
- Chat history retrieval
- Full stack health checks

### Dockerized Testing
We use custom Dockerfiles with cached browsers for consistent CI/CD environments:
- `Dockerfile.test`: Component tests (isolated)
- Full stack via `docker-compose.test.yml` for E2E

```bash
# From project root
./run-ci.sh   # Fast unit + component tests
./run-e2e.sh  # Full integration tests
```
