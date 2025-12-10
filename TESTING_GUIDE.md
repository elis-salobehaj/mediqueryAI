# End-to-End Testing Guide

## Test Plan for AI Healthcare Data Agent

### Prerequisites for Docker Testing

**Docker is NOT currently installed on this system.**

To test the Docker setup, you need to:
1. Install Docker Desktop from: https://www.docker.com/products/docker-desktop
2. Restart your computer after installation
3. Run `.\docker-start.ps1` to start all services

---

## Manual Testing (Current Running Services)

Since Docker is not installed, we'll test the currently running services:
- Backend: http://localhost:8000
- Frontend: http://localhost:5174 (or 5173)

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

## Docker Testing (When Docker is Installed)

### Step 1: Start Services

```powershell
# Run the quick start script
.\docker-start.ps1

# Or manually:
docker-compose up -d
docker exec -it mediquery-ai-ollama ollama pull qwen2.5:3b
```

### Step 2: Verify Services

```powershell
# Check all services are running
docker-compose ps

# Expected output:
# NAME                    STATUS
# antigravity-backend     Up (healthy)
# antigravity-frontend    Up (healthy)
# mediquery-ai-ollama      Up (healthy)
```

### Step 3: Test Endpoints

```powershell
# Test backend health
curl http://localhost:8000/health

# Expected: {"status":"healthy","service":"antigravity-backend",...}

# Test Ollama
curl http://localhost:11434/api/tags

# Expected: List of installed models including qwen2.5:3b

# Test frontend
curl http://localhost:3000

# Expected: HTML content
```

### Step 4: Run Query Tests

Open http://localhost:3000 and run all 8 test queries above.

### Step 5: Test Local Model

```powershell
# Verify local model is being used
docker-compose logs backend | Select-String "local"

# Expected: "Using local Ollama model: qwen2.5:3b"
```

### Step 6: Switch to Cloud Mode

```powershell
# Edit .env
# Change: USE_LOCAL_MODEL=false
# Add: GEMINI_API_KEY=your_actual_key or ANTHROPIC_API_KEY=your_actual_key

# Restart backend
docker-compose restart backend

# Verify cloud mode
docker-compose logs backend | Select-String "Gemini"

# Expected: "Using Google Gemini API"
```

---

## Performance Tests

### Response Time Test

Run 10 queries and measure average response time:

```
Query 1: "Show patient count by state" - Expected: < 3s
Query 2: "List all patients" - Expected: < 2s
Query 3: "Distribution by gender" - Expected: < 2s
...
```

**Target:**
- Local Model (Qwen2.5): 1-3 seconds
- Cloud Model (Gemini): 1-2 seconds

### Load Test

```powershell
# Send 10 concurrent requests
# (Requires Apache Bench or similar tool)
ab -n 100 -c 10 http://localhost:8000/health
```

**Target:** 100% success rate

---

## Integration Tests

### Test Chat History Persistence

1. Ask: "Show patient count by state"
2. Refresh the page
3. Verify chat history is still visible
4. Expected: Previous conversation persists

### Test Chart Type Switching

1. Ask: "Distribution of patients by gender"
2. Click "Bar" button above chart
3. Verify chart changes to bar chart
4. Click "Donut" button
5. Verify chart changes to donut chart

### Test Model Switching

1. Select "GEMMA 3 27B" or "GEMINI 2.5 FLASH LITE" from dropdown
2. Ask a query
3. Select "Gemini Pro" from dropdown
4. Ask the same query
5. Verify both work (if cloud mode enabled)

---

## Docker-Specific Tests

### Volume Persistence Test

```powershell
# Create some chat history
# Stop containers
docker-compose down

# Start again
docker-compose up -d

# Verify:
# - Ollama model still installed
# - Chat history still present
```

### Health Check Test

```powershell
# Check health status
docker inspect antigravity-backend | Select-String "Health"

# Expected: "Status": "healthy"
```

### Resource Usage Test

```powershell
# Monitor resource usage
docker stats

# Expected:
# mediquery-ai-ollama: ~2-4GB RAM
# antigravity-backend: ~500MB RAM
# antigravity-frontend: ~50MB RAM
```

---

## Test Results Template

```
Date: ___________
Tester: ___________
Environment: [ ] Docker [ ] Manual

Test 1: Basic Query
Status: [ ] Pass [ ] Fail
Notes: ___________

Test 2: Pie Chart
Status: [ ] Pass [ ] Fail
Notes: ___________

Test 3: Case-Insensitive
Status: [ ] Pass [ ] Fail
Notes: ___________

Test 4: Scatter Plot
Status: [ ] Pass [ ] Fail
Notes: ___________

Test 5: Hierarchical
Status: [ ] Pass [ ] Fail
Notes: ___________

Test 6: Box Plot
Status: [ ] Pass [ ] Fail
Notes: ___________

Test 7: Choropleth Map
Status: [ ] Pass [ ] Fail
Notes: ___________

Test 8: Time Series
Status: [ ] Pass [ ] Fail
Notes: ___________

Overall Status: [ ] All Pass [ ] Some Failures
```

---

## Known Limitations

1. **Docker Required**: Full testing requires Docker Desktop
2. **Model Download**: First run requires ~2GB download for Qwen2.5
3. **RAM Requirements**: Minimum 8GB RAM recommended for Docker setup
4. **Windows**: PowerShell execution policy may need adjustment

---

## Next Steps

1. **Install Docker Desktop** (if testing Docker setup)
2. **Run Manual Tests** (using current running services)
3. **Document Results** (use template above)
4. **Report Issues** (create GitHub issues for any failures)

---

## Quick Manual Test (No Docker)

Since Docker is not installed, test with current services:

```powershell
# Open browser to:
http://localhost:5174

# Run these queries:
1. "Show patient count by state"
2. "Distribution of patients by gender"
3. "List all patients with diabetes"
4. "Show relationship between age and BMI"
5. "Show patients by insurance type and income bracket"

# Verify:
- All queries return data
- Visualizations render correctly
- Chart type switching works
- Patient names (not IDs) are shown
- Case-insensitive search works
```

**This can be done RIGHT NOW without Docker!**
