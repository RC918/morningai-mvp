import { config } from 'dotenv';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

// Get __dirname in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Parse command line arguments
const args = process.argv.slice(2);
const envFileIndex = args.indexOf('--env-file');
const appIndex = args.indexOf('--app');

let envFile = '.env';
let app = 'default';

if (envFileIndex !== -1 && envFileIndex + 1 < args.length) {
  envFile = args[envFileIndex + 1];
}

if (appIndex !== -1 && appIndex + 1 < args.length) {
  app = args[appIndex + 1];
}

// Load environment variables from specified file
config({ path: envFile });

console.log(`🔍 Checking environment for app: ${app}`);
console.log(`📁 Using env file: ${envFile}`);

// Load secrets matrix
const matrixPath = join(__dirname, '..', 'SECRETS_MATRIX.csv');
const matrixCsv = readFileSync(matrixPath, 'utf-8');
const matrix = matrixCsv.split('\n').slice(1).map(line => {
  const [app, variable, required] = line.split(',');
  return { app, variable, required: required === 'TRUE' };
});

// Get required variables for the current app
const required = matrix
  .filter(row => row.app === app && row.required)
  .map(row => row.variable);

let missing = [];
for (const key of required) {
  if (!process.env[key] || String(process.env[key]).trim() === '') missing.push(key);
}

if (missing.length) {
  console.error('❌ Missing required environment variables:\n' + missing.map(k => `- ${k}`).join('\n'));
  process.exit(1);
}

const urlish = ['SUPABASE_URL', 'DATABASE_URL', 'REDIS_URL', 'NEXT_PUBLIC_SUPABASE_URL'];
for (const k of urlish) {
  if (required.includes(k)) {
    try { new URL(process.env[k]); } catch { console.warn(`⚠️ ${k} may be malformed: ${process.env[k]}`); }
  }
}

if (required.includes('JWT_SECRET') && (process.env.JWT_SECRET || '').length < 24) {
  console.warn('⚠️ JWT_SECRET should be at least 24 chars.');
}

console.log('✅ Env check passed.');


