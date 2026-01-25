# Testing Guide

## Automated Testing (Docker - Recommended)

We provide two dedicated test suites that run in isolated Docker containers:

### CI Tests (Fast - Unit & Component)

```bash
# Linux/Mac
./run-ci.sh

# Windows
.\run-ci.ps1
```

**What it runs (~30 seconds):**
1. **Backend Unit Tests** - 13 pytest tests for API logic, auth, and LLM integration
2. **Frontend Component Tests** - 10 Playwright tests for React components

**Use case:** Run before every commit, in CI/CD pipelines

### E2E Tests (Full Stack Integration)

```bash
# Linux/Mac
./run-e2e.sh

# Windows
.\run-e2e.ps1
```

**What it runs (~2-3 minutes):**
1. Spins up full stack (backend + frontend + database)
2. Runs Playwright E2E tests against real services
3. Tests complete user flows (login, queries, visualizations)

**Use case:** Run before merging PRs, deployment validation

---

## Manual Testing (Current Running Services)

### Test Model Switching

1. Select "GEMMA 3 27B" or "GEMINI 2.5 FLASH LITE" from dropdown
2. Ask a query
3. Select "Gemini Pro" from dropdown
4. Ask the same query
5. Verify both work (if cloud mode enabled)

### Test Average Metric Aggregation

1. Ask: "Show average age of patients by state"
2. Switch visualization to "Indicator"
3. Verify the number displayed is reasonable (e.g., ~40-60) and NOT a huge sum (e.g., >1000).
4. Verify the label says "Avg age" or similar.

### Test Suite

#### Test 1: Basic Query (Bar Chart)
**Query:** "Show patient count by state"
**Expected:**
- Chart Type: Bar or Choropleth Map
- Data: Patient counts grouped by state
- Interactive: Can switch between bar, pie, map views

#### Test 2: Pie Chart
**Query:** "Distribution of patients by gender"
**Expected:**
- Chart Type: Pie
- Data: Male, Female, Other percentages
- Interactive: Can switch to donut or bar

#### Test 3: Case-Insensitive Search
**Query:** "List all patients with diabetes"
**Expected:**
- Finds patients with "Diabetes" (capital D)
- Shows patient NAMES not IDs
- Table or list view

#### Test 4: Scatter Plot
**Query:** "Show relationship between age and BMI"
**Expected:**
- Chart Type: Scatter
- X-axis: Age
- Y-axis: BMI
- Can switch to heatmap or line

#### Test 5: Hierarchical Chart
**Query:** "Show patients by insurance type and income bracket"
**Expected:**
- Chart Type: Sunburst or Treemap
- Hierarchical structure visible
- Interactive drill-down

#### Test 6: Box Plot
**Query:** "Distribution of patient ages"
**Expected:**
- Chart Type: Box plot
- Shows quartiles and outliers
- Can switch to violin or histogram

#### Test 7: Choropleth Map
**Query:** "Patient count by state on a map"
**Expected:**
- Chart Type: Choropleth (USA map)
- Color-coded states
- Hover shows state name and count

#### Test 8: Time Series
**Query:** "Patient registrations by date"
**Expected:**
- Chart Type: Line chart
- X-axis: Dates
- Y-axis: Count
- Can switch to area chart

---