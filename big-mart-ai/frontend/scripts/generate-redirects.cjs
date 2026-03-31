/**
 * Generate _redirects file for Netlify.
 * Reads BACKEND_URL from environment (set in Netlify dashboard).
 * Run after `vite build` so the file lands in dist/.
 */
const fs = require('fs');
const path = require('path');

const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
const outDir = path.join(__dirname, '..', 'dist');

const rules = [
  `/api/*  ${backendUrl}/api/:splat  200`,
  `/media/*  ${backendUrl}/media/:splat  200`,
  `/*  /index.html  200`,
].join('\n');

fs.writeFileSync(path.join(outDir, '_redirects'), rules + '\n');
console.log(`✓ Generated _redirects → proxy to ${backendUrl}`);
