#!/usr/bin/env python3
"""Extract English glosses for the target words from the Kaikki Spanish extract.

Source (Wiktextract, Wiktionary-derived — real lexicography, CC BY-SA 4.0):
    https://kaikki.org/dictionary/Spanish/kaikki.org-dictionary-Spanish.jsonl  (~1GB)

Streams stdin (the 1GB JSONL) and keeps only entries whose word is in the
target set, so nothing huge is stored. Emits glosses_raw.json:
    { word: [ {pos, glosses:[...]}, ... ] }  in target-frequency order.

Usage:
    curl -sSL "<url>" | python3 extract_glosses.py _top1000.txt > /dev/null
"""
import json
import sys

# POS values we keep, in display-priority order. Wiktionary uses many; these
# cover the content + function words in a frequency list.
POS_KEEP = {
    "verb", "noun", "adj", "adv", "pron", "prep", "conj", "det", "article",
    "num", "intj", "particle", "name", "phrase",
}
MAX_GLOSSES_PER_POS = 3


def main():
    targets_path = sys.argv[1]
    with open(targets_path, encoding="utf-8") as f:
        order = [w.strip() for w in f if w.strip()]
    targets = set(order)
    found = {}  # word -> {pos: [glosses]}

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        word = e.get("word")
        if word not in targets:
            continue
        pos = e.get("pos")
        if pos not in POS_KEEP:
            continue
        glosses = []
        for sense in e.get("senses", []):
            gl = sense.get("glosses") or sense.get("raw_glosses")
            if gl:
                glosses.append(gl[0])
        if not glosses:
            continue
        bucket = found.setdefault(word, {})
        existing = bucket.setdefault(pos, [])
        for g in glosses:
            if g not in existing and len(existing) < MAX_GLOSSES_PER_POS:
                existing.append(g)

    result = {}
    for w in order:
        if w in found:
            result[w] = [{"pos": pos, "glosses": gl} for pos, gl in found[w].items()]

    with open("glosses_raw.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    missing = [w for w in order if w not in found]
    print(f"matched {len(result)} / {len(order)} target words", file=sys.stderr)
    print(f"missing {len(missing)}: {missing[:30]}{'...' if len(missing) > 30 else ''}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
