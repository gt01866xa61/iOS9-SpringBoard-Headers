#!/usr/bin/env node
/**
 * update-boards.js — fetch each manufacturer's motherboard listings and
 * suggest new boards to add to MoboRefRN/boards.json.
 *
 * Usage (from repo root):
 *   node scripts/update-boards.js
 *
 * This script is best-effort: manufacturer sites have anti-bot protection
 * that can break scraping. If a brand fails, add boards manually to the
 * diff output and re-run with --apply to write boards.json.
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const https = require('https');

const BOARDS_PATH = path.join(__dirname, '..', 'MoboRefRN', 'boards.json');

const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36';

function get(url, timeout = 15000) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { 'User-Agent': UA, Accept: 'text/html,application/xhtml+xml' } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return resolve(get(new URL(res.headers.location, url).toString(), timeout));
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error(`${url}: HTTP ${res.statusCode}`));
      }
      let data = '';
      res.setEncoding('utf8');
      res.on('data', (c) => (data += c));
      res.on('end', () => resolve(data));
    });
    req.on('error', reject);
    req.setTimeout(timeout, () => { req.destroy(new Error('timeout')); });
  });
}

// ASRock sitemap lists every motherboard product page
async function scrapeASRock() {
  const urls = [
    'https://www.asrock.com/sitemap.asp',
    'https://www.asrock.com/mb/index.asp',
  ];
  const found = new Set();
  const boards = [];
  for (const url of urls) {
    try {
      const html = await get(url);
      const rx = /\/mb\/(AMD|Intel)\/([^\/"']+?)\/(?:index\.asp)?["']/g;
      let m;
      while ((m = rx.exec(html)) !== null) {
        const model = decodeURIComponent(m[2]).replace(/\+/g, ' ').trim();
        if (!model || found.has(model)) continue;
        found.add(model);
        const chipset = extractChipset(model);
        if (chipset) boards.push({ brand: 'ASRock', chipset, fullModelName: model });
      }
    } catch (e) {
      console.warn(`  ASRock ${url}: ${e.message}`);
    }
  }
  return boards;
}

// GIGABYTE sitemap
async function scrapeGigabyte() {
  const urls = ['https://www.gigabyte.com/sitemap.xml'];
  const boards = [];
  const found = new Set();
  for (const url of urls) {
    try {
      const xml = await get(url);
      const rx = /\/Motherboard\/([^<"']+)/g;
      let m;
      while ((m = rx.exec(xml)) !== null) {
        let slug = m[1].split('#')[0].split('?')[0].replace(/-rev-\d+$/i, '').trim();
        const model = slug.replace(/-/g, ' ').trim();
        if (!model || found.has(model)) continue;
        found.add(model);
        const chipset = extractChipset(model);
        if (chipset) boards.push({ brand: 'GIGABYTE', chipset, fullModelName: model });
      }
    } catch (e) {
      console.warn(`  GIGABYTE ${url}: ${e.message}`);
    }
  }
  return boards;
}

// MSI sitemap
async function scrapeMSI() {
  const urls = ['https://www.msi.com/sitemap.xml'];
  const boards = [];
  const found = new Set();
  for (const url of urls) {
    try {
      const xml = await get(url);
      const rx = /\/Motherboard\/([^<"']+)/g;
      let m;
      while ((m = rx.exec(xml)) !== null) {
        const slug = m[1].split('#')[0].split('?')[0].trim();
        const model = slug.replace(/-/g, ' ').trim();
        if (!model || found.has(model)) continue;
        found.add(model);
        const chipset = extractChipset(model);
        if (chipset) boards.push({ brand: 'MSI', chipset, fullModelName: model });
      }
    } catch (e) {
      console.warn(`  MSI ${url}: ${e.message}`);
    }
  }
  return boards;
}

// ASUS — their search endpoint
async function scrapeASUS() {
  console.warn('  ASUS: manual update required (heavy anti-bot protection). Skipping.');
  return [];
}

function extractChipset(model) {
  const m = model.toUpperCase().match(/\b([ZHBAX])(\d{3}E?)\b/);
  return m ? m[1] + m[2] : null;
}

function boardId(b) {
  return `${b.brand}::${b.chipset}::${b.fullModelName}`.toLowerCase().replace(/\s+/g, '_');
}

async function main() {
  const current = JSON.parse(fs.readFileSync(BOARDS_PATH, 'utf8'));
  const currentIds = new Set(current.boards.map((b) => b.id));
  console.log(`Current database: ${current.boards.length} boards (v${current.version})`);
  console.log('Fetching from manufacturer sites...\n');

  const [asrock, gigabyte, msi, asus] = await Promise.all([
    scrapeASRock(),
    scrapeGigabyte(),
    scrapeMSI(),
    scrapeASUS(),
  ]);

  const all = [...asrock, ...gigabyte, ...msi, ...asus];
  const newBoards = [];
  for (const b of all) {
    const id = boardId(b);
    if (!currentIds.has(id)) {
      newBoards.push({ id, ...b });
      currentIds.add(id);
    }
  }

  console.log(`\nFound ${newBoards.length} new boards:`);
  for (const b of newBoards.slice(0, 50)) {
    console.log(`  + ${b.brand.padEnd(9)} ${b.chipset.padEnd(7)} ${b.fullModelName}`);
  }
  if (newBoards.length > 50) console.log(`  ... and ${newBoards.length - 50} more`);
  if (newBoards.length === 0) { console.log('Nothing to add.'); return; }

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const answer = await new Promise((r) => rl.question('\nAdd all to boards.json? (y/N) ', r));
  rl.close();
  if (answer.trim().toLowerCase() !== 'y') { console.log('Cancelled.'); return; }

  current.boards.push(...newBoards);
  current.count = current.boards.length;
  current.version = new Date().toISOString().slice(0, 10);
  fs.writeFileSync(BOARDS_PATH, JSON.stringify(current, null, 2));
  console.log(`\nWrote ${current.boards.length} boards to boards.json (v${current.version})`);
  console.log('\nNext steps:');
  console.log('  git add MoboRefRN/boards.json');
  console.log(`  git commit -m "db: add ${newBoards.length} new boards ${current.version}"`);
  console.log('  git push origin claude/build-iphone-app-3HKVs');
}

main().catch((e) => { console.error(e); process.exit(1); });
