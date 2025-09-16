// Run: node scripts/check_env.mjs
const required = [
  'SUPABASE_URL',
  'SUPABASE_ANON_KEY',
  'SUPABASE_SERVICE_ROLE_KEY',
  'SUPABASE_JWT_SECRET',
  'DATABASE_URL',
  'REDIS_URL',
  'JWT_SECRET',
  'EMAIL_FROM',
  'SMTP_HOST','SMTP_PORT','SMTP_USER','SMTP_PASS'
];

let missing = [];
for (const key of required) {
  if (!process.env[key] || String(process.env[key]).trim() === '') missing.push(key);
}

if (missing.length) {
  console.error('❌ Missing required environment variables:\n' + missing.map(k => `- ${k}`).join('\n'));
  process.exit(1);
}

const urlish = ['SUPABASE_URL','DATABASE_URL','REDIS_URL'];
for (const k of urlish) {
  try { new URL(process.env[k]); } catch { console.warn(`⚠️ ${k} may be malformed: ${process.env[k]}`); }
}

if ((process.env.JWT_SECRET || '').length < 24) {
  console.warn('⚠️ JWT_SECRET should be at least 24 chars.');
}

console.log('✅ Env check passed.');
