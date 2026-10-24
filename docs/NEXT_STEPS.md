# ParkFlow AI — Next Steps for Continuation

*Created: 2026-10-24 | For use on the receiving laptop*

---

## What You're Receiving

A complete, portable ParkFlow AI project with:
- ✅ FastAPI backend with 8 API routers, AI routing, WebSocket, IoT simulator
- ✅ Next.js 14 frontend with 7 fully-implemented dashboard pages
- ✅ SQLite database auto-initialized on first startup (no setup needed)
- ✅ 100 parking slots across 3 floors with virtual sensor simulation
- ✅ All documentation and configuration files

---

## Step 1: Extract and Set Up

```bash
# Extract the ZIP
unzip ParkFlow_AI_Transfer.zip
cd parkflow-ai
```

---

## Step 2: Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# macOS / Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# The defaults work out of the box (SQLite, simulation mode)
# Edit .env only if you want PostgreSQL or MQTT
```

### Start the Backend

```bash
# From the backend/ directory with venv active:
python -m app.main

# OR use uvicorn directly:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO: 🚀 ParkFlow AI starting up...
INFO: ✅ Database initialized
INFO: ✅ Database seeded with 100 parking slots across 3 floors
INFO: ✅ IoT simulator started in background
INFO: 🎉 ParkFlow AI ready — http://localhost:8000
```

Verify: http://localhost:8000/health → `{"status":"ok","version":"1.0.0"}`

---

## Step 3: Frontend Setup

```bash
cd frontend

# Install Node.js dependencies (required only once)
npm install

# Start the development server
npm run dev
```

Open: **http://localhost:3000**

---

## Step 4: Run the Demo

1. Keep **both** terminal windows running (backend + frontend)
2. Open http://localhost:3000 in a browser
3. Navigate to **IoT Sensors** page
4. Click **▶ Start Simulator** (5-second interval)
5. Watch the **Dashboard** for live slot updates
6. Go to **Live Parking Map** → click a green slot
7. Go to **AI Navigation** → calculate a route
8. Click **▶ Simulate Drive** to animate the navigation
9. Optionally go to **Reservations** to reserve the slot

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI entry point |
| `backend/app/core/config.py` | All configuration settings |
| `backend/app/db/seed.py` | Database seeding (100 slots) |
| `backend/app/routing/graph.py` | Navigation graph (NetworkX) |
| `backend/app/routing/pathfinder.py` | Dijkstra pathfinding engine |
| `backend/app/iot/simulator.py` | IoT simulator service |
| `backend/app/websocket/manager.py` | WebSocket broadcast |
| `frontend/app/page.tsx` | Main page with routing |
| `frontend/lib/api.ts` | All API calls |
| `frontend/hooks/useWebSocket.ts` | Real-time WebSocket hook |
| `frontend/types/index.ts` | TypeScript definitions |

---

## Commands Reference

### Backend

```bash
# Start server
python -m app.main

# Run tests
cd backend && pytest tests/ -v

# Reset database (delete and restart)
rm parkflow.db && python -m app.main
```

### Frontend

```bash
# Development server
npm run dev

# Type check
npx tsc --noEmit

# Lint
npm run lint

# Production build (optional)
npm run build
```

---

## Environment Variables

**Backend (`.env` in `backend/` or project root):**
```env
DATABASE_URL=sqlite+aiosqlite:///./parkflow.db
IOT_MODE=simulation
SIMULATION_INTERVAL_SECONDS=5
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Frontend (`.env.local` in `frontend/`):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Database Notes

- **SQLite** is the default — no setup needed, file is `backend/parkflow.db`
- The database is **NOT included** in the ZIP — it is recreated automatically on first startup
- **PostgreSQL:** Change `DATABASE_URL` in `.env` and install `asyncpg`: `pip install asyncpg`

---

## Immediate Next Development Tasks

### Priority 1: Verification
- [ ] Confirm backend starts cleanly with all 100 slots seeded
- [ ] Verify frontend loads at localhost:3000
- [ ] Test WebSocket connection (check Sidebar status indicator)
- [ ] Run the IoT simulator and verify slot updates appear in real-time

### Priority 2: Optional Enhancements
- [ ] Add reservation auto-expiry background task
- [ ] Implement `sessions.py` API for navigation session tracking
- [ ] Add Arduino/ESP32 firmware to `iot/arduino/`
- [ ] Create Docker Compose for one-command startup
- [ ] Add Alembic migration files (`alembic revision --autogenerate`)

### Priority 3: Production Prep
- [ ] Switch to PostgreSQL
- [ ] Add user authentication (JWT)
- [ ] Deploy to cloud (Railway, Render, or Vercel)

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version (need 3.11+)
python --version

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Check for import errors
python -c "from app.main import app; print('OK')"
```

### Frontend fails to compile
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run dev
```

### WebSocket shows "Disconnected"
- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_WS_URL=ws://localhost:8000` in frontend `.env.local`
- Check browser console for WebSocket errors

### "Backend Not Reachable" error in dashboard
- Start the backend: `cd backend && python -m app.main`
- Verify http://localhost:8000/health responds with `{"status":"ok"}`
- Check CORS settings in `.env` (`ALLOWED_ORIGINS`)

### Database is empty (no slots)
```bash
# Reset the database
cd backend
rm -f parkflow.db
python -m app.main  # Will re-seed automatically
```

---

## Optional Integrations

### MQTT (Physical Sensors)
1. Install Mosquitto broker
2. Set `MQTT_BROKER_HOST=localhost` in `.env`
3. Set `IOT_MODE=mqtt` or `hybrid`
4. Flash ESP32 firmware (see `iot/arduino/`)

### ThingSpeak (Cloud IoT)
1. Create ThingSpeak channel
2. Set `THINGSPEAK_CHANNEL_ID` and `THINGSPEAK_READ_API_KEY` in `.env`
3. Set `IOT_MODE=thingspeak`

---

*Good luck continuing development! The project is feature-complete for demo mode.*
