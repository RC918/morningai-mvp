
# ENVIRONMENT VARIABLES – MorningAI (No AWS)

This document lists **all required/optional environment variables** across **Local, GitHub, Vercel, Render, Supabase**.

> **Scope**: AWS is **not used** currently.

---

## 1) Naming & Profiles
- Use three profiles: **local**, **staging**, **production**
- Files:
  - `.env.local` – local development (never commit)
  - `.env.staging` – optional local override for staging testing
  - `.env.production` – optional local override for production testing
  - `env.sample` – template checked into git (no secrets)

---

## 2) Variables (by category)

### Core
| Key | Required | Example | Notes |
|---|---|---|---|
| `NODE_ENV` | Yes | `production` | `development`/`staging`/`production` |
| `APP_NAME` | Yes | `morningai` | Used in logs/metrics |
| `NEXT_PUBLIC_APP_URL` | Yes | `https://morningai.me` | Public URL for links/callbacks |
| `NEXT_PUBLIC_API_URL` | Yes | `https://api.morningai.me` | Used by frontend to call API |

### Supabase / Database
| Key | Required | Example | Notes |
|---|---|---|---|
| `SUPABASE_URL` | Yes | `https://xxxx.supabase.co` | Project URL |
| `SUPABASE_ANON_KEY` | Yes | `ey...` | Client‑side public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | `ey...` | **Server only** – RLS bypass (protect) |
| `SUPABASE_JWT_SECRET` | Yes | `supersecret` | Must match Supabase Auth settings |
| `DATABASE_URL` | Yes | `postgresql://...` | Prefer **pooler** URL with `sslmode=require&channel_binding=disable` |

### Redis
| Key | Required | Example | Notes |
|---|---|---|---|
| `REDIS_URL` | Yes | `redis://default:pass@host:6379` | Used for lockout, JWT blacklist, rate limiting, sessions |

### Auth / Security
| Key | Required | Example | Notes |
|---|---|---|---|
| `JWT_SECRET` | Yes | `longrandomstring` | For app‑issued tokens |
| `ENCRYPTION_KEY` | Optional | 32 bytes | For data‑at‑rest encryption (hex/base64) |
| `TOTP_ISSUER` | Optional | `MorningAI` | 2FA TOTP label |

### Email
| Key | Required | Example | Notes |
|---|---|---|---|
| `EMAIL_FROM` | Yes | `Morning AI <no-reply@morningai.me>` | Display name + email |
| `SMTP_HOST` | Yes | `smtp.mailgun.org` |  |
| `SMTP_PORT` | Yes | `587` | 587(TLS) or 465(SSL) |
| `SMTP_USER` | Yes | `postmaster@...` |  |
| `SMTP_PASS` | Yes | `app-password` |  |
| `SMTP_SECURE` | Optional | `false` | `true` for 465 |

### OAuth
Only set the providers you actually use.
| Key | Required | Example |
|---|---|---|
| `GOOGLE_CLIENT_ID` | Optional |  |
| `GOOGLE_CLIENT_SECRET` | Optional |  |
| `GITHUB_CLIENT_ID` | Optional |  |
| `GITHUB_CLIENT_SECRET` | Optional |  |
| `LINE_CHANNEL_ID` | Optional |  |
| `LINE_CHANNEL_SECRET` | Optional |  |

### Billing
| Key | Required | Notes |
|---|---|---|
| `STRIPE_SECRET_KEY` | Optional | Required if Stripe is enabled |
| `STRIPE_WEBHOOK_SECRET` | Optional |  |
| `TAPPAY_PARTNER_KEY` | Optional | Required if TapPay is enabled |
| `TAPPAY_MERCHANT_ID` | Optional |  |

### Observability
| Key | Required | Notes |
|---|---|---|
| `SENTRY_DSN` | Optional | |
| `LOG_LEVEL` | Optional | `debug`/`info`/`warn`/`error` |

### Feature Flags
| Key | Required | Default |
|---|---|---|
| `FEATURE_ENABLE_HITL` | Optional | `true` |
| `FEATURE_ENABLE_MARKETPLACE` | Optional | `false` |

---

## 3) Where to set them

### Local
- Create `.env.local` from `env.sample`
- Never commit `.env.local`

### GitHub (Actions → Secrets and variables → **Actions**)
- Create repository secrets for CI (build/test only if needed)
- Name suggestions: `SB_URL`, `SB_ANON_KEY`, `REDIS_URL`, `JWT_SECRET`, `STRIPE_SECRET_KEY`, ...

### Vercel
- Project → Settings → Environment Variables
- Add for **Development / Preview / Production**
- Ensure **NEXT_PUBLIC_*** vars are also present in Vercel (client-readable)

### Render (if used for API)
- Service → Environment → Environment Variables
- Map same keys; restart service to apply

### Supabase
- Project Settings → API: copy `URL`, `anon key`, `service_role key`
- Authentication settings → `JWT secret` must match `SUPABASE_JWT_SECRET`

---

## 4) Verification Checklist
- Local `npm run dev` starts with no missing env errors
- Staging deploy passes **Env Check** step (see workflow below)
- `/health/env-check` endpoint returns `{ ok: true }` with internal checks:
  - DB connect OK
  - Redis connect OK
  - JWT secret length OK
  - SMTP login OK (optional ping)

---

## 5) Rotation & Access
- Rotate high-privilege keys every 90 days
- Restrict access: service-role key only on server
- Keep an **access log** of who updated which secret and when

