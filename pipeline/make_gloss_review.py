#!/usr/bin/env python3
"""Turn raw Kaikki glosses into a review-ready sheet for the gloss hand pass.

Reads glosses_raw.json (extract_glosses.py) + lemma_pos.json (add_lemma_pos.py)
+ an ordered word list. Uses spaCy's dominant POS per word to pick the primary
gloss from the matching Kaikki POS bucket, so grammatical words draw the right
sense (no -> adverb "not", es -> verb "to be") instead of a stray noun sense.

Emits, in rank order:
    glosses_review.tsv        all 1000 rows
    glosses_review_top300.tsv the priority pass (first 300)
Columns: rank  word  spacy_pos  draft_gloss  final_gloss  needs_review  all_candidates
The reviewer fills final_gloss ONLY to override the draft (blank = accept it).
needs_review flags rows the POS-guided pick could not resolve confidently.

Human review decisions live in gloss_overrides.json (word -> final gloss), so
they survive regeneration; final_gloss is pre-filled from it here.
"""
import json
import sys

# glosses that carry no standalone learner meaning for a frequency list:
# form-of/inflection noise, plus letter-name and misspelling senses that
# Wiktionary attaches to short high-frequency words (de -> "letter D").
FORMOF_MARKERS = (
    "inflection of", "first-person", "second-person", "third-person",
    "singular of", "plural of", "apocopic form of", "feminine of",
    "masculine of", "diminutive of", "augmentative of", "form of",
    "name of the latin script letter", "name of the letter", "greek letter",
    "misspelling of", "the name of the",
)
# fallback order when spaCy's POS bucket is absent: content words first
POS_PRIORITY = ["noun", "verb", "adj", "adv", "prep", "conj", "pron",
                "det", "article", "num", "intj", "particle", "name", "phrase"]
# spaCy pos_label -> candidate Kaikki POS buckets (first match wins)
SPACY_TO_KAIKKI = {
    "noun": ["noun"], "verb": ["verb"], "adjective": ["adj"],
    "adverb": ["adv"], "pronoun": ["pron"], "preposition": ["prep"],
    "conjunction": ["conj"], "determiner": ["det", "article"],
    "number": ["num"], "interjection": ["intj"], "particle": ["particle"],
}

# Contractions/abbreviations Kaikki has no lemma entry for (kept via the
# filter_list allowlist). Glosses are unambiguous, so pre-fill them.
MANUAL_GLOSSES = {
    "del":   ("contraction", "of the; from the (de + el)"),
    "al":    ("contraction", "to the; at the (a + el)"),
    "sr.":   ("abbr", "Mr. (abbreviation of señor)"),
    "sra.":  ("abbr", "Mrs.; Ms. (abbreviation of señora)"),
    "dr.":   ("abbr", "Dr. (abbreviation of doctor)"),
    "ud.":   ("abbr", "you (formal); abbreviation of usted"),
    "srta.": ("abbr", "Miss (abbreviation of señorita)"),
}


def is_formof(g):
    low = g.lower()
    return any(m in low for m in FORMOF_MARKERS)


def clean(g):
    return g.rstrip(":").strip()


def first_real_gloss(glosses):
    for g in glosses:
        if not is_formof(g):
            return clean(g)
    return None


def best_gloss(entries, spacy_label):
    """First real gloss from the spaCy-matched bucket, else by priority. None if all form-of."""
    by_pos = {e["pos"]: e["glosses"] for e in entries}
    for bucket in SPACY_TO_KAIKKI.get(spacy_label, []):
        if bucket in by_pos:
            g = first_real_gloss(by_pos[bucket])
            if g:
                return g, False           # confident: matched dominant POS
    for pos in sorted(by_pos, key=lambda p: POS_PRIORITY.index(p)
                      if p in POS_PRIORITY else 99):
        g = first_real_gloss(by_pos[pos])
        if g:
            return g, True                # fell back to another POS -> confirm
    return None, True


def pick_draft(word, entries, spacy_label, lemma, raw):
    """Return (draft_gloss, flag). flag: '' confident, 'L' lemma-resolved, 'Y' needs attention."""
    g, fell_back = best_gloss(entries, spacy_label)
    if g and not fell_back:
        return g, ""
    # inflected form with only form-of senses: resolve from the lemma's gloss
    if lemma and lemma != word and lemma in raw:
        lg, _ = best_gloss(raw[lemma], spacy_label)
        if lg:
            return lg, "L"
    if g:
        return g, "Y"
    first = next(iter({e["pos"]: e["glosses"] for e in entries}.values()))
    return clean(first[0]), "Y"


def main():
    targets_path = sys.argv[1]
    with open(targets_path, encoding="utf-8") as f:
        order = [w.strip() for w in f if w.strip()]
    raw = json.load(open("glosses_raw.json", encoding="utf-8"))
    pos_data = json.load(open("lemma_pos.json", encoding="utf-8"))
    try:
        overrides = json.load(open("gloss_overrides.json", encoding="utf-8"))
    except FileNotFoundError:
        overrides = {}

    rows = []
    counts = {"": 0, "L": 0, "Y": 0}
    for rank, word in enumerate(order, 1):
        info = pos_data.get(word, {})
        spacy_label = info.get("pos_label", "")
        lemma = info.get("lemma", "")
        final = overrides.get(word, "")
        if word in MANUAL_GLOSSES:
            _, primary = MANUAL_GLOSSES[word]
            rows.append((rank, word, spacy_label, primary, final, "", f"{primary}"))
            counts[""] += 1
            continue
        entries = raw.get(word)
        if not entries:
            rows.append((rank, word, spacy_label, "", final, "Y-MISSING", ""))
            counts["Y"] += 1
            continue
        primary, flag = pick_draft(word, entries, spacy_label, lemma, raw)
        cand = " || ".join(
            f"[{e['pos']}] " + " | ".join(e["glosses"]) for e in entries)
        counts[flag] += 1
        rows.append((rank, word, spacy_label, primary, final, flag, cand))

    header = "rank\tword\tspacy_pos\tdraft_gloss\tfinal_gloss\tneeds_review\tall_candidates\n"

    def write(path, subset):
        with open(path, "w", encoding="utf-8") as f:
            f.write(header)
            for r in subset:
                f.write("\t".join(str(x) for x in r) + "\n")

    write("glosses_review.tsv", rows)
    write("glosses_review_top300.tsv", rows[:300])

    def tally(subset):
        c = {"": 0, "L": 0, "Y": 0}
        for r in subset:
            c[r[5] if r[5] in c else "Y"] += 1
        return c

    full, top = tally(rows), tally(rows[:300])
    print(f"glosses_review.tsv:        {len(rows)} rows | "
          f"confident {full['']} | lemma-resolved(L) {full['L']} | needs-attention(Y) {full['Y']}",
          file=sys.stderr)
    print(f"glosses_review_top300.tsv: 300 rows | "
          f"confident {top['']} | lemma-resolved(L) {top['L']} | needs-attention(Y) {top['Y']}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
