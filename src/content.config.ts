import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// The 22 content pages (20 SEO + privacypolicy + terms), ported from Jekyll _pages/.
// Frontmatter mirrors the Jekyll files; `layout` is accepted but unused (Astro routes
// via [...slug].astro). Legal pages have no permalink → slug derives from the filename,
// matching Jekyll's collection permalink `/:path/`.
const pages = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/pages' }),
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    permalink: z.string().optional(),
    layout: z.string().optional(),
    include_in_header: z.boolean().optional(),
    include_in_footer: z.boolean().optional(),
    include_in_learn_more: z.boolean().optional(),
  }),
});

export const collections = { pages };
