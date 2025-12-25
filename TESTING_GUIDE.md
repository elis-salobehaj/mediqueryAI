# End-to-End Testing Guide

## Automated Testing (Docker - Recommended)

We have a dedicated test suite that runs inside Docker containers, nsuring a consistent environment isolated from your local machine.

### Quick Start

```powershell
# Windows (PowerShell)
.\run-tests.ps1

# Linux / Mac (Bash)
chmod +x run-tests.sh
./run-tests.sh
```

This script will:
1. Build the test containers (caching dependencies for speed).
2. Run **Pytest** for the backend logic and LLM integrations.
3. Run **Playwright** component tests for the frontend.

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