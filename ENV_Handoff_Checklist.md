
# 🔐 Environment Variables – Handoff Checklist (MorningAI)

## Scope
Unify and verify environment variables across **Local / Staging / Production** (no AWS in scope).

---

## A. Files to include in the repo
- `/env.sample`
- `/ENVIRONMENT_VARIABLES.md`
- `/scripts/check_env.mjs`
- `/.github/workflows/env-check.yml`

---

## B. Local setup (developer laptop)
1. Duplicate `env.sample` → `.env.local`
2. Fill **local** values (use staging keys only if needed)
3. Run:
   ```bash
   node -v   # Node 20+
   npm i
   export $(cat .env.local | xargs) && node scripts/check_env.mjs
   npm run dev
   ```
4. Expect: `✅ Env check passed.` and app boots

---

## C. Staging setup
### Vercel (Frontend) / Render (API) – choose what you use
- Add the **same keys** as in `env.sample`
- For Vercel: set for **Development / Preview / Production** separately
- For Render: Service → Environment → Variables → add keys then **Restart**

### GitHub Actions
- Go to **Settings → Secrets and variables → Actions**
- Create: `SB_URL`, `SB_ANON_KEY`, `SB_SERVICE_ROLE_KEY`, `SB_JWT_SECRET`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `EMAIL_FROM`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`
- Run workflow: **Env Check**

---

## D. Production setup
- Mirror staging keys with **production** credentials
- Add `/health/env-check` endpoint (returns `{ ok: true }` or errors)
- Enable alerting (on failed DB/Redis/JWT checks)

---

## E. Verification matrix
- Local:
  - DB connect ✓
  - Redis connect ✓
  - JWT secret length ✓
  - SMTP login (optional) ✓
- Staging:
  - PR triggers **Env Check** workflow ✓
  - App boots with staging secrets ✓
- Production:
  - Health endpoint green ✓
  - Rotation policy in place ✓

---

## F. Deliverables (attach to Handoff Package)
- `env.sample` (final)
- `ENVIRONMENT_VARIABLES.md` (final)
- Screenshot / logs of:
  - Vercel/Render env list
  - GitHub Actions **Env Check** passed
  - `/health/env-check` response
