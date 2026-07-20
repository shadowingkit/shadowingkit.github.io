#!/usr/bin/env python3
"""Export words.json to the ungated CSV download.

Writes public/frequency/spanish-1000-most-common-words.csv so Astro serves it at
shadowingkit.com/frequency/spanish-1000-most-common-words.csv. Free, no gate.
"""
import csv
import json
import os

FIELDS = ["rank", "word", "gloss", "pos", "lemma", "ipa", "syllables", "stress"]
OUT = os.path.join("..", "public", "frequency", "spanish-1000-most-common-words.csv")


def main():
    words = json.load(open("words.json", encoding="utf-8"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for row in words:
            w.writerow({k: row[k] for k in FIELDS})
    print(f"wrote {OUT}: {len(words)} rows")


if __name__ == "__main__":
    main()
