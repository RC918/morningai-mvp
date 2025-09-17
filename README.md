# MorningAI MVP (Monorepo)

This repository hosts the MorningAI MVP in a monorepo layout.

## Structure
- `apps/web` – Frontend (Next.js/React)
- `apps/api` – Backend (API service)
- `infra/*` – Deployment & infrastructure configs (Vercel/Render/Supabase/Terraform)
- `.github/workflows` – CI/CD pipelines
- `ops/env` – Environment variable standards & scripts
- `docs` – Blueprints, reviews, security modules, and handoff packs

## Quickstart
1. Copy `ops/env/env.sample` to `.env.local` under each app and fill values.
2. Run the env check:
   ```bash
   node ops/env/scripts/check_env.mjs --env-file apps/web/.env --app web
   node ops/env/scripts/check_env.mjs --env-file apps/api/.env --app api
   ```
3. Install & build each app.



## CI Status

[![Env Check](https://github.com/RC918/morningai-mvp/actions/workflows/env-check.yml/badge.svg)](https://github.com/RC918/morningai-mvp/actions/workflows/env-check.yml)




## Code Coverage

[![Codecov](https://codecov.io/gh/RC918/morningai-mvp/branch/main/graph/badge.svg)](https://codecov.io/gh/RC918/morningai-mvp)

*(請替換為您專案的實際 Codecov 徽章 URL)*




## Deployment Status

![Deploy](https://github.com/RC918/morningai-mvp/actions/workflows/deploy.yml/badge.svg)

*(請替換為您專案的實際部署工作流程徽章 URL)*


