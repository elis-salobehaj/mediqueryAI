# MediQuery AI - Frontend

The futuristic interface for the MediQuery AI healthcare data agent. Built with React 19, Vite, and Tailwind CSS.

## 🌟 Key Features

- **Cyberpunk / Sci-Fi Aesthetic**: Dark mode glassmorphism UI.
- **Explainable AI Interface**: 
  - Displays the agent's **"Thinking Process"** in a collapsible detail view.
  - Shows Raw SQL generation steps.
  - Transparent error handling.
- **Dynamic Visualization Engine**:
  - `PlotlyVisualizer.tsx` component automatically selects 1 of 60+ chart types based on data.
  - Interactive zooming, panning, and exporting.
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

- `src/components/`: Reusable UI components
  - `ChatBox.tsx`: The heart of the app. Handles user input, keeps chat history, and displays the **Thinking Process**.
  - `PlotlyVisualizer.tsx`: The brain of the visualization logic.
- `src/App.tsx`: Main layout wrapper.
- `src/index.css`: Global styles and Tailwind directives.

## 🧪 Testing

We use **Playwright** for End-to-End and Component testing.

```bash
# Run Component Tests (including ChatBox thinking process)
npm run test-ct

# Run E2E Tests
npm run test-e2e
```
