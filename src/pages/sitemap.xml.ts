import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { pageUrl } from '../lib/pages';

// Single /sitemap.xml matching the jekyll-sitemap output: same path (referenced by
// robots.txt and submitted to Search Console), same urlset schema, absolute <loc>s
// for the homepage + all content pages. lastmod is the build time (jekyll used file
// mtime; the parity check compares the <loc> set, not lastmod).
export const GET: APIRoute = async ({ site }) => {
  const base = site!.href; // https://shadowingkit.com/
  const pages = await getCollection('pages');
  const locs = [
    new URL('/', base).href,
    ...pages.map((p) => new URL(pageUrl(p), base).href),
  ].sort();

  const lastmod = new Date().toISOString();
  const body =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd" xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    locs
      .map((loc) => `<url>\n<loc>${loc}</loc>\n<lastmod>${lastmod}</lastmod>\n</url>`)
      .join('\n') +
    `\n</urlset>`;

  return new Response(body, {
    headers: { 'Content-Type': 'application/xml' },
  });
};
