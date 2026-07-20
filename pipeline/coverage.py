#!/usr/bin/env python3
"""Cumulative frequency coverage against the FULL corpus.

The honest denominator is the full corpus, not es_50k. es_50k truncates the
long tail, which overstates how much of the language the top-N words cover.

Corpus: Hermit Dave FrequencyWords, Spanish, OpenSubtitles 2018 (CC BY-SA 4.0).
    https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/es/es_full.txt

Usage:
    python3 coverage.py [corpus=es_full.txt]   # prints table + writes coverage.json

If the corpus file is absent, download it first:
    curl -sSL -o es_full.txt "<url above>"
"""
import json
import os
import sys

RANKS = [100, 500, 1000, 2000, 5000, 10000]


def load_counts(path):
    counts = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.split()
            if len(p) >= 2 and p[1].isdigit():
                counts.append(int(p[1]))
    return counts


def coverage(counts, ranks):
    total = sum(counts)
    out, cum = {}, 0
    ceiling = max(ranks)
    for i, c in enumerate(counts, 1):
        cum += c
        if i in ranks:
            out[i] = round(100 * cum / total, 2)
        if i >= ceiling:
            break
    return total, out


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "es_full.txt"
    if not os.path.exists(path):
        sys.exit(f"corpus not found: {path}\nsee module docstring for the download command")
    counts = load_counts(path)
    total, cov = coverage(counts, RANKS)
    print(f"total tokens (denominator): {total:,}")
    print(f"total word types:           {len(counts):,}\n")
    for r in RANKS:
        print(f"  top-{r:<6} covers {cov[r]:6.2f}%")
    result = {
        "corpus": "hermitdave FrequencyWords es_full (OpenSubtitles 2018)",
        "total_tokens": total,
        "total_types": len(counts),
        "coverage_pct": cov,
    }
    with open("coverage.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("\nwrote coverage.json")
