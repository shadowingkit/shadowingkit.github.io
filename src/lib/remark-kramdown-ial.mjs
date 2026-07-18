import { visit } from 'unist-util-visit';

// The Jekyll content used Kramdown's Inline Attribute List syntax to open internal
// links in the same tab (needed because <base target="_blank"> defaults everything to
// a new tab): `[text](/url){:target="_self"}`. remark does not understand IAL and would
// render the literal `{:target="_self"}` as text. Every IAL in the corpus is exactly
// this one attribute, so this plugin sets target="_self" on the preceding link and
// strips the marker. Must run BEFORE remark-smartypants (which would curl the quotes).
export function remarkKramdownIAL() {
  const MARKER = /\{:target="_self"\}/g;
  return (tree) => {
    visit(tree, 'text', (node, index, parent) => {
      if (!parent || typeof index !== 'number') return;
      if (!node.value.includes('{:target="_self"}')) return;
      const prev = parent.children[index - 1];
      if (prev && prev.type === 'link') {
        prev.data = prev.data || {};
        prev.data.hProperties = { ...(prev.data.hProperties || {}), target: '_self' };
      }
      node.value = node.value.replace(MARKER, '');
    });
  };
}
