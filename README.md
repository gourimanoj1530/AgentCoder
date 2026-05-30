# AgentCoder 🤖

An agentic AI coding assistant built with **LangGraph**, **FastAPI**, **React**, and deployed on **AWS ECS Fargate**.

**Live Demo:** http://15.206.117.81 | **API Docs:** http://15.206.117.81:8000/docs

---

## Overview

AgentCoder is a full-stack AI-powered IDE that uses a **LangGraph ReAct agent** to autonomously reason, write, execute, and debug Python code. Users describe a coding problem in natural language and the agent iterates through a plan → reason → act → observe → output loop until it produces a working solution.

---

## Architecture

### Backend — LangGraph ReAct Agent

```
User Query
    ↓
Planner Node       → breaks problem into steps
    ↓
Reasoner Node      → selects tool and forms action
    ↓
Tool Executor      → runs one of 3 tools
    ├── Code Executor   (subprocess Python runner)
    ├── Web Search      (Tavily API)
    └── Doc Lookup      (pydoc + PyPI fallback)
    ↓
Observer Node      → reads output, decides next step
    ↓
Output Node        → formats final response
```

### Agent Tools

| Tool | Description |
|---|---|
| `run_code` | Executes Python in a sandboxed subprocess with safety checks |
| `web_search` | Searches the web via Tavily for docs, examples, and current info |
| `doc_lookup` | Looks up Python package documentation via pydoc and PyPI |

### Full Stack

```
React Frontend (Monaco Editor)
        ↓ REST + WebSocket
FastAPI Backend
        ↓
LangGraph Agent ──→ Tools
        ↓
PostgreSQL (AWS RDS)    Firebase Auth
```

---

## Features

- **Monaco Editor** — VS Code-grade editor with syntax highlighting for 40+ languages
- **Live Linting** — Real-time pyflakes linting via WebSocket
- **5 Themes** — Midnight, Aurora, Ember, Arctic, Neon
- **File Tree** — Create, edit, and organize project files
- **ZIP Download** — Export your entire project
- **Auth** — Google Sign-In and Email/Password via Firebase
- **Persistent Projects** — Projects and files stored in PostgreSQL

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Monaco Editor, React Router |
| Styling | Custom CSS themes |
| Auth | Firebase (Google + Email/Password) |
| Backend | FastAPI, Python 3.11 |
| AI Agent | LangGraph, Groq (llama-3.3-70b) |
| Tools | Tavily Search, pydoc, subprocess |
| Database | PostgreSQL (SQLAlchemy ORM) |
| Linting | WebSocket + pyflakes |
| Tracing | LangSmith |
| Containers | Docker (multi-stage builds) |
| Registry | AWS ECR |
| Compute | AWS ECS Fargate |
| Database Host | AWS RDS PostgreSQL |
| Web Server | nginx |

---

## Project Structure

```
agentcoder/
├── api/
│   ├── main.py          # FastAPI app entry point
│   ├── routes.py        # Auth, projects, files CRUD
│   └── ws.py            # WebSocket live linting
├── graph/
│   ├── graph.py         # LangGraph StateGraph builder
│   ├── nodes.py         # Agent node functions
│   ├── state.py         # AgentState TypedDict
│   └── edges.py         # Routing logic
├── llm/
│   └── client.py        # Groq LLM client + prompt templates
├── tools/
│   ├── executor.py      # Python code executor
│   ├── search.py        # Tavily web search
│   └── docs.py          # pydoc + PyPI lookup
├── db/
│   ├── models.py        # User, Project, File models
│   └── database.py      # SQLAlchemy engine + session
├── auth/
│   └── firebase.py      # Firebase Admin token verification
├── memory/
│   └── store.py         # Conversation memory (JSON)
├── tracing/
│   └── langsmith.py     # LangSmith tracing setup
├── agentcoder-frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── CodeEditor.jsx     # Monaco + WebSocket linting
│   │   │   ├── FileTree.jsx
│   │   │   └── Navbar.jsx
│   │   ├── contexts/
│   │   │   ├── AuthContext.jsx
│   │   │   ├── ProjectContext.jsx
│   │   │   └── ThemeContext.jsx
│   │   └── pages/
│   │       ├── LandingPage.jsx    # Animated particle canvas
│   │       ├── LoginPage.jsx
│   │       └── RegisterPage.jsx
│   ├── Dockerfile.react
│   └── nginx.conf
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop
- PostgreSQL

### Backend Setup

```bash
cd agentcoder
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Create .env file
cp env.example .env
# Fill in: GROQ_API_KEY, TAVILY_API_KEY, LANGSMITH_API_KEY,
#          DATABASE_URL, FIREBASE_SERVICE_ACCOUNT (path)

# Start DB container
docker run -d --name agentcoder-db \
  -e POSTGRES_USER=agentcoder \
  -e POSTGRES_PASSWORD=agentcoder123 \
  -e POSTGRES_DB=agentcoder \
  -p 5434:5432 postgres:15

# Start backend
uvicorn api.main:app --reload
```

### Frontend Setup

```bash
cd agentcoder-frontend
npm install
# Set VITE_API_URL=http://localhost:8000 in .env
npm run dev
```

Frontend: http://localhost:5173 | API: http://localhost:8000/docs

---

## AWS Deployment

### Build and Push Docker Images

```bash
# Authenticate with ECR
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin \
  <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com

# Backend
docker-compose build backend
docker tag agentcoder-backend:latest \
  <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/agentcoder:backend
docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/agentcoder:backend

# Frontend
cd agentcoder-frontend
docker build -f Dockerfile.react -t agentcoder-react .
docker tag agentcoder-react:latest \
  <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/agentcoder-frontend:latest
docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/agentcoder-frontend:latest
```

### Deploy to ECS

```bash
aws ecs update-service \
  --cluster agentcoder-cluster \
  --service agentcoder-service \
  --force-new-deployment \
  --region ap-south-1
```

### Infrastructure

| Resource | Details |
|---|---|
| Compute | AWS ECS Fargate (1 vCPU, 2GB RAM) |
| Database | AWS RDS PostgreSQL 15 (db.t3.micro) |
| Registry | AWS ECR (2 repositories) |
| Networking | AWS VPC, public subnets |

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM inference |
| `TAVILY_API_KEY` | Tavily API key for web search |
| `LANGSMITH_API_KEY` | LangSmith tracing key |
| `LANGSMITH_PROJECT` | LangSmith project name |
| `DATABASE_URL` | PostgreSQL connection string |
| `FIREBASE_SERVICE_ACCOUNT` | Path to Firebase service account JSON |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/agent/run` | Run the LangGraph agent |
| GET | `/health` | Health check |
| POST | `/auth/login` | Firebase token verification |
| GET/POST | `/projects` | List / create projects |
| GET/PUT/DELETE | `/projects/{id}` | Project CRUD |
| GET/POST | `/files` | List / create files |
| GET/PUT/DELETE | `/files/{id}` | File CRUD |
| WS | `/ws/lint` | Live pyflakes linting |

---

## Author

**Gouri Manoj** — Final-year B.Tech student, AI & Machine Learning

GitHub: [@gourimanoj1530](https://github.com/gourimanoj1530)
