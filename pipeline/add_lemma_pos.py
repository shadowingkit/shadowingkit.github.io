#!/usr/bin/env python3
"""Add lemma + POS to the clean word list via spaCy es_core_news_sm.

Lemma groups inflected forms (fui -> ir, mujeres -> mujer); POS powers the
site's part-of-speech filter. Input words are isolated (no sentence context),
which spaCy handles well for lemma and acceptably for POS on a frequency list.

Run inside the venv (spaCy is not a repo dependency; the site is static):
    .venv/bin/python add_lemma_pos.py

Reads _clean_words.txt, writes lemma_pos.json: { word: {lemma, pos, pos_label} }.
"""
import json
import spacy

# Universal POS -> user-facing filter label. AUX folded into verb (ser/estar/
# haber/ir read as verbs to a learner); CCONJ/SCONJ into conjunction.
POS_LABEL = {
    "NOUN": "noun", "PROPN": "noun", "VERB": "verb", "AUX": "verb",
    "ADJ": "adjective", "ADV": "adverb", "ADP": "preposition",
    "CCONJ": "conjunction", "SCONJ": "conjunction", "PRON": "pronoun",
    "DET": "determiner", "NUM": "number", "INTJ": "interjection",
    "PART": "particle", "PUNCT": "punctuation", "SYM": "symbol", "X": "other",
}

# spaCy mis-tags contractions/abbreviations (they aren't normal tokens).
# Override the allowlist words to match make_gloss_review.MANUAL_GLOSSES.
# (lemma, pos_label)
MANUAL_POS = {
    "del":   ("del", "contraction"),
    "al":    ("al", "contraction"),
    "sr.":   ("señor", "abbreviation"),
    "sra.":  ("señora", "abbreviation"),
    "dr.":   ("doctor", "abbreviation"),
    "ud.":   ("usted", "abbreviation"),
    "srta.": ("señorita", "abbreviation"),
}


def main():
    words = [w.strip() for w in open("_clean_words.txt", encoding="utf-8") if w.strip()]
    nlp = spacy.load("es_core_news_sm", disable=["parser", "ner"])

    result = {}
    for word, doc in zip(words, nlp.pipe(words)):
        if word in MANUAL_POS:
            lemma, label = MANUAL_POS[word]
            result[word] = {"lemma": lemma, "pos": label.upper(), "pos_label": label}
            continue
        tok = doc[0]
        result[word] = {
            "lemma": tok.lemma_,
            "pos": tok.pos_,
            "pos_label": POS_LABEL.get(tok.pos_, "other"),
        }

    with open("lemma_pos.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    from collections import Counter
    dist = Counter(v["pos_label"] for v in result.values())
    print(f"tagged {len(result)} words")
    for label, n in dist.most_common():
        print(f"  {label:<12} {n}")


if __name__ == "__main__":
    main()
