# Secrets Matrix

## Staging Environment Secrets

| Secret Name             | Description                                     | Example Value (Staging) |
| :---------------------- | :---------------------------------------------- | :---------------------- |
| `SUPABASE_URL`          | Supabase Project URL                            | `https://abc.supabase.co` |
| `SUPABASE_ANON_KEY`     | Supabase Anon Key (Public)                      | `eyJhbGciOiJIUzI1Ni...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key (Admin)               | `eyJhbGciOiJIUzI1Ni...` |
| `SUPABASE_JWT_SECRET`   | Supabase JWT Secret                             | `super-secret-jwt-key` |
| `DATABASE_URL`          | PostgreSQL Database Connection String           | `postgresql://user:pass@host:port/db` |
| `REDIS_URL`             | Redis Connection String (e.g., Upstash)         | `redis://default:token@host:port` |
| `JWT_SECRET`            | Backend API JWT Secret                          | `your-secret-key-change-this-in-production` |
| `EMAIL_FROM`            | Sender email address for notifications          | `no-reply@morningai.com` |
| `SMTP_HOST`             | SMTP Server Host for email sending              | `smtp.sendgrid.net` |
| `SMTP_PORT`             | SMTP Server Port                                | `587` |
| `SMTP_USER`             | SMTP Username                                   | `apikey` |
| `SMTP_PASS`             | SMTP Password                                   | `SG.xxxxxxxxxxxxxxxx` |

## Production Environment Secrets

| Secret Name             | Description                                     | Example Value (Production) |
| :---------------------- | :---------------------------------------------- | :------------------------- |
| `SUPABASE_URL`          | Supabase Project URL                            | `https://xyz.supabase.co` |
| `SUPABASE_ANON_KEY`     | Supabase Anon Key (Public)                      | `eyJhbGciOiJIUzI1Ni...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key (Admin)               | `eyJhbGciOiJIUzI1Ni...` |
| `SUPABASE_JWT_SECRET`   | Supabase JWT Secret                             | `super-duper-secret-jwt-key` |
| `DATABASE_URL`          | PostgreSQL Database Connection String           | `postgresql://produser:prodpass@prodhost:prodport/proddb` |
| `REDIS_URL`             | Redis Connection String (e.g., Upstash)         | `redis://proddefault:prodtoken@prodhost:prodport` |
| `JWT_SECRET`            | Backend API JWT Secret                          | `super-secret-production-jwt-key` |
| `EMAIL_FROM`            | Sender email address for notifications          | `no-reply@morningai.com` |
| `SMTP_HOST`             | SMTP Server Host for email sending              | `smtp.sendgrid.net` |
| `SMTP_PORT`             | SMTP Server Port                                | `587` |
| `SMTP_USER`             | SMTP Username                                   | `apikey` |
| `SMTP_PASS`             | SMTP Password                                   | `SG.yyyyyyyyyyyyyyyy` |


