#!/usr/bin/env python3
"""Merge every enrichment field into words.json — the artifact the site reads.

Inputs (all produced by earlier pipeline steps):
    words_clean.tsv      final_rank, corpus_rank, word  (clean 1000, filtered)
    enrich.py            syllables, stress, IPA          (imported)
    lemma_pos.json       lemma, POS                      (spaCy)
    glosses_review.tsv   draft_gloss + final_gloss       (reviewed)
    pos_overrides.json   word -> POS, optional            (hand corrections)

Gloss per word = final_gloss if the reviewer set one, else the draft.
POS per word = the override if present, else spaCy's label (spaCy mis-tags some
high-frequency forms, e.g. interjections and person-inflected verbs).
Output: words.json = [ {rank, word, gloss, pos, lemma, ipa, syllables, stress} ].
"""
import csv
import json
from enrich import enrich


def main():
    with open("words_clean.tsv", encoding="utf-8") as f:
        clean = list(csv.DictReader(f, delimiter="\t"))

    pos_data = json.load(open("lemma_pos.json", encoding="utf-8"))
    try:
        pos_overrides = json.load(open("pos_overrides.json", encoding="utf-8"))
    except FileNotFoundError:
        pos_overrides = {}

    glosses = {}
    with open("glosses_review.tsv", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            glosses[row["word"]] = row["final_gloss"].strip() or row["draft_gloss"].strip()

    words, missing_gloss = [], []
    for row in clean:
        word = row["word"]
        syllables, stress, ipa = enrich(word)
        gloss = glosses.get(word, "")
        if not gloss:
            missing_gloss.append(word)
        info = pos_data.get(word, {})
        words.append({
            "rank": int(row["final_rank"]),
            "word": word,
            "gloss": gloss,
            "pos": pos_overrides.get(word) or info.get("pos_label", ""),
            "lemma": info.get("lemma", word),
            "ipa": ipa,
            "syllables": syllables,
            "stress": stress,
        })

    with open("words.json", "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    print(f"wrote words.json: {len(words)} words")
    if missing_gloss:
        print(f"WARNING: {len(missing_gloss)} without a gloss: {missing_gloss[:20]}")
    else:
        print("all words have a gloss")


if __name__ == "__main__":
    main()
