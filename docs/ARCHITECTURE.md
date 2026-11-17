# PulsePilot AI Architecture

```
React + TypeScript client
        | Bearer token + JSON
        v
FastAPI routes -> validation -> authentication dependency
        |                         |
        v                         v
SQLite post store          analysis provider adapter
                                  |-- demo rules (always available)
                                  `-- Ollama /api/generate (optional)
```

No browser code reads the database or model configuration. The UI handles loading and failures; the API owns validation, authorization and persistence.
