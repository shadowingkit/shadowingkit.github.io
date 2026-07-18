#!/usr/bin/env node
// Parity harness — the acceptance oracle for the Jekyll → Astro migration.
// Compares the built Astro site (dist/) against a Jekyll baseline (_site/) on the
// SEO-critical surface: route set, per-page <head> model, JSON-LD, static SEO files,
// sitemap loc set, and a trailing-slash guard. Exits nonzero on any diff.
//
// Usage: node scripts/verify-parity.mjs [baselineDir] [distDir]
// Defaults: baseline = ./_site (Jekyll build), dist = ./dist (Astro build).
// The Jekyll baseline must be built with `url: https://shadowingkit.com` set so its
// canonical/OG/sitemap URLs are absolute (as GitHub Pages emits in production);
// otherwise every URL-bearing tag will falsely diff.

import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { load } from 'cheerio';

const BASELINE = process.argv[2] ?? join(process.cwd(), '_site');
const DIST = process.argv[3] ?? join(process.cwd(), 'dist');

let failures = 0;
const fail = (msg) => { failures++; console.error('  ✗ ' + msg); };
const ok = (msg) => console.log('  ✓ ' + msg);

// ---- helpers ----------------------------------------------------------------
function walkHtml(dir) {
  const out = {};
  const rec = (d) => {
    for (const name of readdirSync(d)) {
      const p = join(d, name);
      const s = statSync(p);
      if (s.isDirectory()) rec(p);
      else if (name.endsWith('.html')) {
        // _site/what-is-shadowing/index.html -> /what-is-shadowing/ ; index.html -> /
        let rel = relative(dir, p).split(sep).join('/');
        let route = '/' + rel.replace(/index\.html$/, '').replace(/\.html$/, '');
        if (!route.endsWith('/')) route += '/';
        out[route] = p;
      }
    }
  };
  rec(dir);
  return out;
}

const norm = (s) => (s ?? '').replace(/\s+/g, ' ').trim();

function headModel($) {
  const meta = (sel, attr = 'content') => $(sel).attr(attr);
  const og = (p) => meta(`meta[property="og:${p}"]`);
  const tw = (n) => meta(`meta[name="twitter:${n}"]`);

  const jsonld = $('script[type="application/ld+json"]')
    .map((_, el) => {
      try { return JSON.stringify(sortKeys(JSON.parse($(el).text()))); }
      catch { return 'INVALID_JSON'; }
    })
    .get()
    .sort();

  const preconnect = $('link[rel="preconnect"]')
    .map((_, el) => $(el).attr('href')).get().sort();

  const fa = $('link[rel="stylesheet"][href*="fontawesome"]').first();
  const faModel = fa.length
    ? {
        href: fa.attr('href'),
        integrity: fa.attr('integrity'),
        crossorigin: fa.attr('crossorigin'),
        media: fa.attr('media'),
        onload: norm(fa.attr('onload')),
      }
    : null;

  const gaPresent = $('script[src*="googletagmanager.com/gtag/js"]').length > 0;

  return {
    title: norm($('title').text()),
    description: meta('meta[name="description"]'),
    canonical: $('link[rel="canonical"]').attr('href'),
    favicon: $('link[rel="shortcut icon"]').attr('href'),
    appleItunesApp: meta('meta[name="apple-itunes-app"]'),
    og: { title: og('title'), description: og('description'), image: og('image'), url: og('url'), type: og('type') },
    twitter: { card: tw('card'), title: tw('title'), description: tw('description'), image: tw('image') },
    fontawesome: faModel,
    preconnect,
    gaPresent,
    jsonld,
  };
}

function sortKeys(v) {
  if (Array.isArray(v)) return v.map(sortKeys);
  if (v && typeof v === 'object') {
    return Object.fromEntries(Object.keys(v).sort().map((k) => [k, sortKeys(v[k])]));
  }
  return v;
}

function diffModel(route, a, b) {
  const flat = (obj, prefix = '') =>
    Object.entries(obj).flatMap(([k, val]) =>
      val && typeof val === 'object' && !Array.isArray(val)
        ? flat(val, prefix + k + '.')
        : [[prefix + k, Array.isArray(val) ? JSON.stringify(val) : val]]
    );
  const am = Object.fromEntries(flat(a));
  const bm = Object.fromEntries(flat(b));
  const keys = new Set([...Object.keys(am), ...Object.keys(bm)]);
  let pageFail = 0;
  for (const k of keys) {
    if (String(am[k]) !== String(bm[k])) {
      pageFail++;
      fail(`${route} [${k}]\n      baseline: ${am[k]}\n      astro:    ${bm[k]}`);
    }
  }
  return pageFail;
}

// ---- checks -----------------------------------------------------------------
console.log(`\nBaseline: ${BASELINE}\nDist:     ${DIST}\n`);
if (!existsSync(BASELINE)) { console.error('Baseline missing. Build the Jekyll worktree first.'); process.exit(2); }
if (!existsSync(DIST)) { console.error('dist/ missing. Run `npm run build` first.'); process.exit(2); }

console.log('1. Route set');
const baseRoutes = walkHtml(BASELINE);
const distRoutes = walkHtml(DIST);
const baseSet = new Set(Object.keys(baseRoutes));
const distSet = new Set(Object.keys(distRoutes));
const onlyBase = [...baseSet].filter((r) => !distSet.has(r));
const onlyDist = [...distSet].filter((r) => !baseSet.has(r));
if (onlyBase.length) fail('routes only in baseline: ' + onlyBase.join(', '));
if (onlyDist.length) fail('routes only in astro: ' + onlyDist.join(', '));
if (!onlyBase.length && !onlyDist.length) ok(`${baseSet.size} routes match`);

console.log('2. Per-page <head> model + 3. JSON-LD');
let headFails = 0;
for (const route of [...baseSet].filter((r) => distSet.has(r)).sort()) {
  const a = headModel(load(readFileSync(baseRoutes[route], 'utf8')));
  const b = headModel(load(readFileSync(distRoutes[route], 'utf8')));
  headFails += diffModel(route, a, b);
}
if (!headFails) ok(`head + JSON-LD identical across ${baseSet.size} pages`);

console.log('4. Static SEO files');
for (const f of ['robots.txt', 'llms.txt', 'llms-full.txt', 'CNAME']) {
  const ap = join(BASELINE, f), bp = join(DIST, f);
  // CNAME is excluded from the Jekyll _site; compare dist CNAME to repo CNAME instead.
  const abs = existsSync(ap) ? ap : join(process.cwd(), f);
  if (!existsSync(bp)) { fail(`${f} missing from dist`); continue; }
  if (!existsSync(abs)) { fail(`${f} missing from baseline & repo`); continue; }
  if (norm(readFileSync(abs, 'utf8')) === norm(readFileSync(bp, 'utf8'))) ok(`${f} matches`);
  else fail(`${f} differs`);
}

console.log('5. Sitemap loc set');
const locs = (p) =>
  existsSync(p) ? [...readFileSync(p, 'utf8').matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]).sort() : null;
const baseLocs = locs(join(BASELINE, 'sitemap.xml'));
const distLocs = locs(join(DIST, 'sitemap.xml'));
if (!distLocs) fail('dist/sitemap.xml missing');
else if (!baseLocs) fail('baseline sitemap.xml missing');
else if (JSON.stringify(baseLocs) === JSON.stringify(distLocs)) ok(`${distLocs.length} sitemap locs match`);
else {
  const ob = baseLocs.filter((l) => !distLocs.includes(l));
  const od = distLocs.filter((l) => !baseLocs.includes(l));
  if (ob.length) fail('sitemap locs only in baseline: ' + ob.join(', '));
  if (od.length) fail('sitemap locs only in astro: ' + od.join(', '));
}

console.log('6. Trailing-slash guard (astro canonicals + routes)');
let tsFails = 0;
for (const route of distSet) {
  if (!route.endsWith('/')) { tsFails++; fail(`route without trailing slash: ${route}`); }
  const $ = load(readFileSync(distRoutes[route], 'utf8'));
  const c = $('link[rel="canonical"]').attr('href') || '';
  if (!c.endsWith('/')) { tsFails++; fail(`canonical without trailing slash on ${route}: ${c}`); }
}
if (!tsFails) ok('all routes + canonicals trailing-slashed');

// ---- result -----------------------------------------------------------------
console.log('\n' + (failures ? `❌ ${failures} difference(s) found` : '✅ PARITY: zero diffs'));
process.exit(failures ? 1 : 0);
