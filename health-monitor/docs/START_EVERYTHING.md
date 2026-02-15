# 🚀 Complete Startup Guide - Health Monitor System

This guide provides **step-by-step commands** to start the entire Health Monitor system from scratch.

---

## 📋 Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.12+ installed
- ✅ Docker installed and running
- ✅ Terminal/Command line access

---

## 🔧 Step 1: Start Infrastructure (Docker Containers)

### Start PostgreSQL Database

```bash
docker run -d --name health-monitor-postgres \
  -p 5433:5432 \
  -e POSTGRES_PASSWORD='Postgres@#123$' \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=health_monitor_db \
  postgres:15
```

**Verify it's running:**
```bash
docker ps | grep health-monitor-postgres
```

### Start Redis

```bash
docker run -d --name health-monitor-redis -p 6379:6379 redis
```

**Verify it's running:**
```bash
docker ps | grep health-monitor-redis
```

---

## 🐍 Step 2: Setup Python Environment

### Navigate to project directory
```bash
cd /Users/sachinmishra/Desktop/MCP/health-monitor
```

### Activate virtual environment
```bash
source venv/bin/activate
```

### Install dependencies (if not already installed)
```bash
pip install -r backend/requirements.txt
```

---

## 🖥️ Step 3: Start Backend Services

You'll need **3 separate terminal windows/tabs** for this.

### Terminal 1: FastAPI Backend

```bash
# Navigate to project
cd /Users/sachinmishra/Desktop/MCP/health-monitor

# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

**Verify:** Open http://localhost:8000/docs in your browser

---

### Terminal 2: Rules Engine Worker

```bash
# Navigate to project
cd /Users/sachinmishra/Desktop/MCP/health-monitor

# Activate virtual environment
source venv/bin/activate

# Start worker
cd backend
python workers/rules_engine.py
```

**Expected output:**
```
[WORKER] Starting vitals stream consumer...
```

---

### Terminal 3: Frontend Dashboard (Optional)

```bash
# Navigate to frontend
cd /Users/sachinmishra/Desktop/MCP/health-monitor/frontend

# Start simple HTTP server
python3 -m http.server 3000
```

**Access:** Open http://localhost:3000 in your browser

---

## 🧪 Step 4: Test the System

### Option A: Use the Simulator

Open a **4th terminal**:

```bash
# Navigate to project
cd /Users/sachinmishra/Desktop/MCP/health-monitor

# Activate virtual environment
source venv/bin/activate

# Run simulator
python backend/simulate_vitals.py
```

This will:
- Register/login a test user
- Submit 20 vital signs over 40 seconds
- Trigger alerts for abnormal values

---

### Option B: Manual API Testing

1. Open http://localhost:8000/docs
2. Click on `POST /auth/register`
3. Try it out with:
   ```json
   {
     "username": "testuser",
     "password": "test123"
   }
   ,

   {
    "username":"test_patient",
    "password":"test123"
   }
   ```
4. Copy the `access_token` from the response
5. Click "Authorize" button at the top
6. Enter: `Bearer <your_token_here>`
7. Test `POST /vitals` endpoint

---

## 🔌 Step 5: Start MCP Server (Optional)

For AI agent integration:

```bash
# Navigate to MCP server
cd /Users/sachinmishra/Desktop/MCP/health-monitor/mcp-server

# Activate virtual environment
source ../venv/bin/activate

# Start MCP server
python server.py
```

**Or use MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector python server.py
```

---

## 🛑 Stopping Everything

### Stop Backend Services
Press `Ctrl+C` in each terminal window

### Stop Docker Containers
```bash
docker stop health-monitor-postgres health-monitor-redis
```

### Remove Docker Containers (if needed)
```bash
docker rm health-monitor-postgres health-monitor-redis
```

---

## 🔄 Quick Restart (After First Setup)

If containers already exist:

```bash
# Start containers
docker start health-monitor-postgres health-monitor-redis

# Terminal 1: Backend
cd /Users/sachinmishra/Desktop/MCP/health-monitor
source venv/bin/activate
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Worker
cd /Users/sachinmishra/Desktop/MCP/health-monitor
source venv/bin/activate
cd backend && python workers/rules_engine.py

# Terminal 3: Frontend (optional)
cd /Users/sachinmishra/Desktop/MCP/health-monitor/frontend
python3 -m http.server 3000
```

---

## 📊 Verify Everything is Running

### Check Services
- ✅ Backend API: http://localhost:8000/docs
- ✅ Frontend: http://localhost:3000
- ✅ PostgreSQL: `docker ps | grep postgres`
- ✅ Redis: `docker ps | grep redis`

### Check Logs
- Backend: Check Terminal 1 for HTTP requests
- Worker: Check Terminal 2 for `[WORKER]` and `[ALERT]` messages
- Database: `docker logs health-monitor-postgres`
- Redis: `docker logs health-monitor-redis`

---

## ⚠️ Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Database Connection Failed
```bash
# Check if container is running
docker ps | grep postgres

# Check logs
docker logs health-monitor-postgres

# Restart container
docker restart health-monitor-postgres
```

### Worker Not Processing Events
- Ensure Redis is running: `docker ps | grep redis`
- Check backend is publishing: Look for `INFO: POST /vitals` in Terminal 1
- Restart worker: `Ctrl+C` and run again

---

## 🎯 Success Indicators

You'll know everything is working when:

1. ✅ Backend shows: `Application startup complete`
2. ✅ Worker shows: `Starting vitals stream consumer...`
3. ✅ Simulator shows: `✓ Submitted: heart_rate = 75`
4. ✅ Worker shows: `[ALERT] HEART_RATE alert: 135 gt 120`
5. ✅ Frontend dashboard displays real-time vitals

---

**🎉 You're all set! The Health Monitor system is now running.**
