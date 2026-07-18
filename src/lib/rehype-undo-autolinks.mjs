import { visit } from 'unist-util-visit';

// remark-gfm autolinks bare emails and URLs (autolink literals), e.g. it turns the
// support email in the legal pages into a mailto: link. Kramdown did not do this, so
// to preserve parity this unwraps links that are autolink literals — those whose href
// is exactly `mailto:<text>` or equal to the visible text (bare URL). Authored links
// `[label](url)` have a descriptive label != href and are left untouched.
function nodeText(node) {
  if (node.type === 'text') return node.value;
  return (node.children || []).map(nodeText).join('');
}

export function rehypeUndoAutolinks() {
  return (tree) => {
    visit(tree, 'element', (node, index, parent) => {
      if (node.tagName !== 'a' || !parent || typeof index !== 'number') return;
      const href = node.properties?.href;
      if (typeof href !== 'string') return;
      const text = nodeText(node);
      const isAutolink =
        href === `mailto:${text}` ||
        href === text ||
        href === `http://${text}` ||
        href === `https://${text}`;
      if (isAutolink) {
        parent.children.splice(index, 1, { type: 'text', value: text });
        return index;
      }
    });
  };
}
