# MorningAI MVP (Seed)

This is a cleaned seed extracted from the legacy package.
- apps/web: Vite + React (shadcn/tailwind)
- apps/api: Flask API (replace SQLite with Postgres)
- infra: Dockerfiles and docker-compose
- .github/workflows: CI stub

## Local (Docker)
```
cd infra
docker compose up --build
```

API: http://localhost:8000  
Web: http://localhost:5173
