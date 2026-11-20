# PulsePilot AI - Social Media Content Intelligence

PulsePilot AI is a full-stack, portfolio-ready social media analytics and content intelligence platform. Built with a modern **React + TypeScript** frontend, a high-performance **FastAPI** backend, and a **MongoDB** document database, it orchestrates AI-driven content analysis across **Google Gemini (Cloud AI)** and **Ollama (Localhost AI)**.

---

## 🌟 Key Features

- **Full-Stack Authentication & Security**: Custom PBKDF2 password hashing with cryptographically signed, time-limited JWT bearer tokens.
- **Dynamic Multi-Provider AI Architecture**:
  - **Google Gemini**: Cloud-based content intelligence using `gemini-1.5-flash` with JSON schema enforcement and multimodal image analysis.
  - **Ollama**: Private, local inference (`llama3.2` / `llama3.2-vision:11b`) running on localhost with automated error diagnostics.
  - **In-App Model Switching**: Switch seamlessly between Gemini and Ollama right from the composer UI.
- **Persistent MongoDB Data Layer**:
  - User accounts and authentication credentials.
  - User query history and structured AI analytics.
  - Saved posts, performance metrics, and draft status.
  - File attachments (PDF text extraction with PyPDF and image uploads).
- **Graceful Error Diagnostics**: Transparent error reporting for model timeouts, missing API keys, unreachable Ollama instances, and database connectivity.
- **Production-Ready Structure**: Monorepo with isolated `backend/` and `frontend/` folders, ready for Docker, Vercel, and Cloud deployments.

---

## 📁 Repository Structure

```text
socialmedia_resume/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # REST Endpoints (/auth, /posts, /queries, /analysis, /uploads)
│   │   ├── core/             # Configuration, Settings & PBKDF2/JWT Security
│   │   ├── db/               # MongoDB driver & connection pooling
│   │   ├── schemas/          # Pydantic data validation contracts
│   │   └── services/         # Multi-provider AI orchestration (Gemini, Ollama, Demo)
│   ├── tests/                # Automated pytest API & authentication test suite
│   ├── .env.example          # Environment variable template
│   ├── Dockerfile            # Container configuration for backend
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React + TypeScript Client
│   ├── src/
│   │   ├── api/              # Typed fetch API client (multipart-safe)
│   │   ├── main.tsx          # Dashboard, composer, AI selector, history & auth UI
│   │   └── styles.css        # Responsive dark-theme styling
│   ├── Dockerfile            # Container configuration for frontend
│   └── package.json          # Node dependencies & Vite build scripts
├── docs/                     # Architecture diagrams and specifications
├── reports/                  # Project reports and synopsis
├── docker-compose.yml        # Multi-container orchestration (MongoDB + API + Web)
└── README.md                 # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+** & npm
- **MongoDB** (running locally via `brew services start mongodb-community`, Docker, or a free [MongoDB Atlas](https://www.mongodb.com/atlas) cluster)
- *(Optional)* **Ollama** installed from [ollama.ai](https://ollama.ai) (for local AI inference)
- *(Optional)* **Gemini API Key** from [Google AI Studio](https://aistudio.google.com) (for cloud AI inference)

---

### 2. Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
```

Edit `backend/.env` with your settings:
```ini
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=pulsepilot
JWT_SECRET=your-random-32-character-secret-key

# AI Configuration
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Start the FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```
*API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.*

---

### 3. Frontend Setup

In a new terminal window:
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```
*The React application will open at `http://localhost:5173`.*

---

### 4. Running with Docker Compose

To start MongoDB, the FastAPI backend, and the React frontend in a single command:
```bash
docker compose up --build
```

---

## 🧪 Testing & Quality Assurance

Run the automated test suite covering authentication, multi-provider AI routing, validation, and error states:
```bash
# From the root directory:
PYTHONPATH=. backend/.venv/bin/pytest backend/tests/test_api.py -v

# Test frontend build:
npm --prefix frontend run build
```

---

## 📌 Team & Project Info
- **Project**: PulsePilot AI - Social Media Content Intelligence
- **Team**: Arvind Khanna & Team
- **Stack**: React, TypeScript, FastAPI, MongoDB, Gemini API, Ollama, Pytest, Docker
