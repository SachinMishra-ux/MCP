#!/bin/bash

# 🚀 Health Monitor - Quick Start Script
# This script starts all required services for the Health Monitor system

set -e  # Exit on error

echo "🏥 Health Monitor - Starting All Services"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="/Users/sachinmishra/Desktop/MCP/health-monitor"

# Step 1: Check Docker
echo -e "${YELLOW}Step 1: Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is installed${NC}"
echo ""

# Step 2: Start PostgreSQL
echo -e "${YELLOW}Step 2: Starting PostgreSQL...${NC}"
if docker ps -a | grep -q health-monitor-postgres; then
    echo "Container exists, starting..."
    docker start health-monitor-postgres
else
    echo "Creating new container..."
    docker run -d --name health-monitor-postgres \
        -p 5433:5432 \
        -e POSTGRES_PASSWORD='Postgres@#123$' \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_DB=health_monitor_db \
        postgres:15
fi
echo -e "${GREEN}✅ PostgreSQL started on port 5433${NC}"
echo ""

# Step 3: Start Redis
echo -e "${YELLOW}Step 3: Starting Redis...${NC}"
if docker ps -a | grep -q health-monitor-redis; then
    echo "Container exists, starting..."
    docker start health-monitor-redis
else
    echo "Creating new container..."
    docker run -d --name health-monitor-redis -p 6379:6379 redis
fi
echo -e "${GREEN}✅ Redis started on port 6379${NC}"
echo ""

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 5
echo ""

# Step 4: Instructions for backend
echo -e "${YELLOW}Step 4: Start Backend Services${NC}"
echo "You need to open 3 separate terminal windows and run:"
echo ""
echo -e "${GREEN}Terminal 1 - FastAPI Backend:${NC}"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo -e "${GREEN}Terminal 2 - Rules Engine Worker:${NC}"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  cd backend && python workers/rules_engine.py"
echo ""
echo -e "${GREEN}Terminal 3 - Frontend (Optional):${NC}"
echo "  cd $PROJECT_DIR/frontend"
echo "  python3 -m http.server 3000"
echo ""

# Step 5: Verify
echo -e "${YELLOW}Step 5: Verify Services${NC}"
echo "After starting the backend, verify:"
echo "  - Backend API: http://localhost:8000/docs"
echo "  - Frontend: http://localhost:3000"
echo ""

# Step 6: Test
echo -e "${YELLOW}Step 6: Test the System${NC}"
echo "Run the simulator in a 4th terminal:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  python backend/simulate_vitals.py"
echo ""

echo -e "${GREEN}=========================================="
echo "🎉 Infrastructure is ready!"
echo "Follow the instructions above to start the backend services."
echo "==========================================${NC}"
