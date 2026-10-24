# ParkFlow AI — Smart Parking & Indoor Navigation Ecosystem

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=nextdotjs)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A full-stack smart parking management system with AI-powered indoor navigation, real-time IoT sensor simulation, and a professional dashboard.

---

## Features

- 🗺 **Interactive 3-Floor Parking Map** — 100 slots (34 + 33 + 33) with real-time availability
- 🧭 **AI Navigation Engine** — Dijkstra's shortest path with turn-by-turn instructions
- 📡 **Virtual IoT Simulator** — 100 HC-SR04 ultrasonic sensors (no hardware required)
- 🔄 **WebSocket Real-time Updates** — Live slot status push to all connected clients
- 📋 **Reservation System** — Reserve slots with configurable duration
- 📊 **Analytics Dashboard** — Recharts-powered charts and event timelines
- 🐳 **SQLite by default** — Zero-config local development; PostgreSQL-ready for production

---

## Project Structure

```
parkflow-ai/
├── backend/                   # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── core/config.py     # Pydantic settings
│   │   ├── db/                # Database setup and seed
│   │   ├── models/            # SQLAlchemy models (7 models)
│   │   ├── api/v1/            # REST API endpoints (8 routers)
│   │   ├── routing/           # NetworkX AI pathfinding
│   │   ├── services/          # Occupancy service
│   │   ├── iot/               # IoT simulator
│   │   └── websocket/         # WebSocket manager
│   ├── requirements.txt
│   └── tests/
├── frontend/                  # Next.js 14 + TypeScript
│   ├── app/                   # App router (layout + page)
│   ├── components/
│   │   ├── layout/            # Sidebar + TopNav
│   │   ├── pages/             # 7 dashboard pages
│   │   └── ui/                # Toast component
│   ├── hooks/useWebSocket.ts
│   ├── lib/api.ts             # API client
│   ├── types/index.ts         # TypeScript types
│   └── package.json
├── iot/                       # IoT integrations
│   ├── simulator/             # Python standalone simulator
│   ├── arduino/               # ESP32 firmware blueprint
│   ├── mqtt/                  # MQTT bridge
│   ├── thingspeak/            # ThingSpeak client
│   └── nodered/               # Node-RED flows
├── docs/                      # Documentation
│   ├── SETUP.md
│   ├── PROJECT_STATUS.md
│   └── NEXT_STEPS.md
├── .env.example               # Environment template
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+ (with pip)
- Node.js 18+ (with npm)
- Git (optional)

### 1. Clone / Extract

```bash
# If cloning:
git clone <repo-url> parkflow-ai
cd parkflow-ai

# If from ZIP:
unzip ParkFlow_AI_Transfer.zip
cd parkflow-ai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env if needed (defaults work out of the box)

# Start backend
python -m app.main
```

Backend will be available at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

The database initializes automatically on first start with 100 parking slots.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional, defaults work)
# Copy to .env.local if needed:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

---

## Running the Full Demo

1. Start backend (terminal 1): `cd backend && python -m app.main`
2. Start frontend (terminal 2): `cd frontend && npm run dev`
3. Open browser: http://localhost:3000
4. Navigate to **IoT Sensors** → Click **Start Demo Sequence**
5. Watch the parking map update in real-time!

### Demo Workflow

1. Open Dashboard — see 100 slots across 3 floors
2. Click **Live Parking Map** → select an available slot (green)
3. Click **AI Navigation** → calculate route with turn-by-turn directions
4. Click **Simulate Drive** to animate through the navigation steps
5. Click **IoT Sensors** → **Start Simulator** to trigger real-time updates
6. Watch WebSocket updates push to all connected dashboard tabs
7. Go to **Reservations** → reserve the selected slot

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/slots` | List all slots (filterable) |
| GET | `/api/v1/slots/availability` | Occupancy summary |
| POST | `/api/v1/routes` | Calculate AI route |
| POST | `/api/v1/reservations` | Create reservation |
| GET | `/api/v1/analytics/overview` | Analytics overview |
| POST | `/api/v1/iot/simulation/start` | Start IoT simulator |
| POST | `/api/v1/iot/simulation/trigger` | Trigger slot event |
| WS | `/ws` | Real-time WebSocket |

Full interactive docs: http://localhost:8000/docs

---

## Environment Variables

Copy `.env.example` to `.env` (backend) and `.env.local` (frontend):

```bash
# Database (SQLite default, zero config)
DATABASE_URL=sqlite+aiosqlite:///./parkflow.db

# IoT Mode: simulation | mqtt | thingspeak | hybrid
IOT_MODE=simulation

# Frontend API URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Optional — ThingSpeak
THINGSPEAK_CHANNEL_ID=
THINGSPEAK_READ_API_KEY=

# Optional — MQTT
MQTT_BROKER_HOST=
MQTT_BROKER_PORT=1883
```

---

## Architecture

```
Browser (Next.js)
    │
    ├── REST API (FastAPI) ─── SQLite / PostgreSQL
    │       │
    │       ├── NetworkX Graph (AI Routing)
    │       ├── OccupancyService (State Machine)
    │       └── IoT Simulator (100 virtual sensors)
    │
    └── WebSocket (/ws) ─── Real-time slot updates
```

---

## Development

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend type check
cd frontend
npx tsc --noEmit

# Frontend lint
npm run lint
```

---

## IoT Hardware (Optional)

The system works fully without hardware using the built-in simulator.
For real ESP32 + HC-SR04 sensors, see [docs/SETUP.md](docs/SETUP.md).

---

## License

MIT License — see [LICENSE](LICENSE)

Built with ❤️ for the ParkFlow AI project.
