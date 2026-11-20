# PulsePilot AI Architecture

```text
React + TypeScript Client (Vite)
        │
        ▼ [Bearer JWT + JSON / Multipart Form]
FastAPI Application Layer (/api)
  ├── Middleware (CORS, Request Error Handling)
  ├── Security Layer (PBKDF2 Password Hashing, JWT Tokens)
  └── Router Endpoints:
        ├── /auth (register, login)
        ├── /posts (create, list user posts)
        ├── /queries (query history & AI recommendations)
        ├── /uploads (PDF text extraction, image attachments)
        └── /analysis (AI content intelligence orchestration)
              │
              ├──► MongoDB Database Layer (Users, Queries, Posts, Attachments)
              │
              └──► AI Provider Adapter:
                    ├── Google Gemini API (gemini-1.5-flash / cloud multimodal)
                    ├── Ollama Local API (llama3.2 / localhost:11434)
                    └── Deterministic Demo Analyzer (offline / unit testing)
```

### Architectural Guarantees:
1. **Zero Database Access from Browser**: The client interacts purely through typed HTTP REST endpoints with signed bearer tokens.
2. **Provider Agnostic**: The frontend requests analysis with a chosen provider (`gemini` or `ollama`); the backend validates credentials, adapts the payload structure (including multimodal vision attachments), parses LLM output into validated JSON, and persists both query and result to MongoDB.
3. **Resilient Failure Modes**: Unreachable Ollama servers, missing Gemini keys, or database interruptions yield actionable, structured HTTP error messages (`400`, `502`, `503`, `504`) with diagnostic guidance.
