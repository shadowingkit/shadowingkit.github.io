// Single source of truth for site metadata, links, features, and theme.
// Ported 1:1 from the former Jekyll _config.yml. Components read from here.
//
// NOTE: theme colors are duplicated in src/styles/_theme.scss because SCSS cannot
// import TS at compile time and the stylesheet consumes them via rgba($var, $alpha),
// which needs compile-time Sass values. This object is the canonical copy; keep
// _theme.scss in sync with it.

export const site = {
  // <title> fallback for pages without their own title (i.e. the homepage).
  pageTitle: 'ShadowingKit. Speak Spanish, stop only understanding it',
} as const;

export const app = {
  name: 'ShadowingKit',
  iosAppId: '6476920610',
  iosAppCountry: 'us',
  appStoreLink: 'https://apps.apple.com/app/id6476920610',
  playStoreLink: '',
  pressKitDownloadLink: '',
  icon: '/assets/appicon.png',
  price: '',
  description:
    'The Spanish learning app built around the shadowing technique. 100+ curated native-speaker episodes plus AI-powered content creation. Break through production freeze and speak with natural rhythm.',
} as const;

// Distinct fallback strings the Jekyll head used when a page had no title/description.
// These only apply to the homepage; content pages always set their own. Kept verbatim
// so the ported <head> is byte-equivalent.
export const seoDefaults = {
  ogTitle: 'ShadowingKit – Learn to Speak Spanish, Not Just Understand It',
  ogDescription:
    'The proven shadowing technique, 100+ native-speaker episodes, and AI content creation. Break through production freeze and sound natural in Spanish.',
  twitterTitle: 'ShadowingKit – Speak Spanish Naturally',
  twitterDescription:
    '100+ native-speaker episodes + AI transcription. The shadowing technique for A2–B2 Spanish learners.',
  ogImage: '/assets/og-image.png',
} as const;

export interface Feature {
  title: string;
  description: string;
  fontawesomeIconName: string;
}

export const features: Feature[] = [
  {
    title: 'Speak, stop only understanding',
    description:
      'Break through "production freeze", the moment you understand Spanish perfectly but can\'t get a single word out. Shadowing trains your speech reflexes alongside your vocabulary.',
    fontawesomeIconName: 'comments',
  },
  {
    title: '100+ Native Speaker Episodes',
    description:
      'A curated library of Spanish audio recorded by a native speaker. Latin American history, cultural icons, modern phenomena. Structured by proficiency from A2 beginner to B2 intermediate.',
    fontawesomeIconName: 'headphones',
  },
  {
    title: 'Practice with Any Spanish Content',
    description:
      'Import audio from TikTok, Instagram, or any video file. The app auto-transcribes it and turns it into the same synchronized shadowing experience as the curated library.',
    fontawesomeIconName: 'upload',
  },
];

export const social = {
  yourName: '',
  yourLink: '',
  yourCity: '',
  emailAddress: 'shadowifyapp@gmail.com',
  facebookUsername: '',
  instagramUsername: '',
  twitterUsername: '',
  githubUsername: '',
  youtubeUsername: '',
  mastodonLink: '',
} as const;

export const flags = {
  enableSmartAppBanner: true,
} as const;

export const analytics = {
  googleAnalyticsId: 'G-QJK3ED0N0G',
} as const;

// Theme values (mirror of the Hum token block in src/styles/_tokens.scss, which is
// the canonical copy consumed by all CSS). Kept for reference and future use by
// components. Full token set (tints, shadows, spacing) lives in _tokens.scss.
export const theme = {
  paper: 'oklch(97% 0.012 95)',
  paper2: 'oklch(94% 0.016 95)',
  ink: 'oklch(20% 0.012 250)',
  ink2: 'oklch(42% 0.018 250)',
  accentPear: 'oklch(86% 0.18 95)',
  accentCyan: 'oklch(66% 0.18 235)',
  accentCyanDeep: 'oklch(44% 0.13 235)',
  accentCoral: 'oklch(68% 0.24 18)',
  fontDisplay: '"Plus Jakarta Sans", "Geist", ui-rounded, system-ui, sans-serif',
  fontBody: '"Plus Jakarta Sans", "Geist", ui-rounded, system-ui, sans-serif',
  fontLabel: '"JetBrains Mono", ui-monospace, monospace',
} as const;
