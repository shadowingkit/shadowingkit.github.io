#!/usr/bin/env python3
"""Filter subtitle noise from the frequency list and backfill to 1000.

The OpenSubtitles corpus carries non-Spanish tokens in its high ranks:
English proper names (John, York), English words (the, ok, you), bare
letters (s), and Spanish place/person names (Londres, Jesús). None are
learner vocabulary; shipping them undercuts the list's credibility.

Signal: a real Spanish common word has a lowercase Wiktionary/Kaikki entry.
Proper nouns are capitalized in Kaikki but lowercase in the corpus, so they
fall out naturally. The only legitimate Spanish tokens Kaikki omits are
contractions and abbreviations, kept via an explicit allowlist.

Rule: KEEP if (word has a Kaikki gloss) OR (word in ALLOWLIST); else DROP.
Take the first 1000 keepers in corpus-frequency order and renumber 1..1000.

Reads: _top1300.txt (ordered pool), glosses_raw.json (Kaikki matches).
Writes: words_clean.tsv (final_rank, corpus_rank, word), dropped.tsv (audit).
"""
import json

# Legitimate Spanish tokens Kaikki has no lemma entry for. Kept deliberately.
ALLOWLIST = {"del", "al", "sr.", "sra.", "dr.", "ud.", "srta.", "uds.", "dra."}
TARGET = 1000


def main():
    order = [w.strip() for w in open("_top1300.txt", encoding="utf-8") if w.strip()]
    matched = set(json.load(open("glosses_raw.json", encoding="utf-8")))

    keepers, dropped = [], []
    for corpus_rank, word in enumerate(order, 1):
        if word in matched or word in ALLOWLIST:
            if len(keepers) < TARGET:
                keepers.append((corpus_rank, word))
        else:
            dropped.append((corpus_rank, word))
        if len(keepers) == TARGET:
            # stop consuming the pool once we have 1000 clean words
            last_consumed = corpus_rank
            break
    else:
        last_consumed = len(order)

    # only report drops that fell within the consumed span
    dropped = [(r, w) for r, w in dropped if r <= last_consumed]

    with open("words_clean.tsv", "w", encoding="utf-8") as f:
        f.write("final_rank\tcorpus_rank\tword\n")
        for final_rank, (corpus_rank, word) in enumerate(keepers, 1):
            f.write(f"{final_rank}\t{corpus_rank}\t{word}\n")

    with open("dropped.tsv", "w", encoding="utf-8") as f:
        f.write("corpus_rank\tword\n")
        for corpus_rank, word in dropped:
            f.write(f"{corpus_rank}\t{word}\n")

    # ordered clean word list for downstream steps (glosses, enrichment)
    with open("_clean_words.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(w for _, w in keepers))

    print(f"kept {len(keepers)} clean words (consumed corpus ranks 1..{last_consumed})")
    print(f"dropped {len(dropped)} noise tokens:")
    for corpus_rank, word in dropped:
        print(f"  {corpus_rank:>4}  {word}")


if __name__ == "__main__":
    main()
