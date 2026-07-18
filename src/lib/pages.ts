import { getCollection, type CollectionEntry } from 'astro:content';

export type PageEntry = CollectionEntry<'pages'>;

// URL for a page entry: explicit permalink, else /:id/ (matches Jekyll's collection
// permalink `/:path/`). Always trailing-slashed.
export function pageUrl(entry: PageEntry): string {
  return entry.data.permalink ?? `/${entry.id}/`;
}

// Slug param for [...slug].astro (no leading/trailing slash).
export function pageSlug(entry: PageEntry): string {
  return pageUrl(entry).replace(/^\/|\/$/g, '');
}

// Entries filtered by an include_* flag, sorted alphabetically by id to match the
// order Jekyll iterated site.pages (verified against the baseline build).
export async function pagesWithFlag(
  flag: 'include_in_header' | 'include_in_footer' | 'include_in_learn_more'
): Promise<PageEntry[]> {
  const all = await getCollection('pages');
  return all
    .filter((p) => p.data[flag] === true)
    .sort((a, b) => a.id.localeCompare(b.id));
}
