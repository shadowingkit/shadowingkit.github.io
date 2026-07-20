# Enrichment pipeline

Generates `words.json` (the data the site renders) and the public CSV from the
raw frequency corpus. Pure-Python, plus spaCy for lemma/POS. Everything here is
reproducible; the large/derived intermediates are git-ignored and regenerated
by the steps below.

## Data sources

- **Frequency corpus:** Hermit Dave FrequencyWords, Spanish, OpenSubtitles 2018
  (CC BY-SA 4.0). `es_50k.txt` (top 50k) is committed; `es_full.txt` (~14 MB,
  the full list, needed only for coverage) is fetched on demand.
- **English meanings:** Wiktionary via the Kaikki (Wiktextract) Spanish extract
  (~1 GB, streamed and filtered, never stored whole). Also CC BY-SA.

## Setup

spaCy has no Python 3.14 wheels yet, so the lemma/POS step uses a 3.12 venv:

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m spacy download es_core_news_sm
```

The other steps run on any Python 3. Run everything from this `pipeline/` dir.

## Regeneration order

Each step writes files the later steps read.

```sh
# 1. Phonetics: syllables, stress, IPA (rule-based). Guard it first.
python3 test_enrich.py                       # 30/30 hand-verified cases

# 2. Coverage % against the FULL corpus (honest denominator).
curl -sSL -o es_full.txt \
  https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/es/es_full.txt
python3 coverage.py                          # -> coverage.json

# 3. Target pool: the top 1300 surface words (headroom for the noise filter).
python3 -c "print('\n'.join(l.split()[0] for l in open('es_50k.txt')))" | head -1300 > _top1300.txt

# 4. English glosses: stream the 1 GB Kaikki extract, keep only our words.
curl -sSL https://kaikki.org/dictionary/Spanish/kaikki.org-dictionary-Spanish.jsonl \
  | python3 extract_glosses.py _top1300.txt  # -> glosses_raw.json

# 5. Drop subtitle noise (English names, "the", "ok", bare letters) and
#    backfill to a clean 1000. -> words_clean.tsv, _clean_words.txt, dropped.tsv
python3 filter_list.py

# 6. Lemma + POS (needs the venv). -> lemma_pos.json
.venv/bin/python add_lemma_pos.py

# 7. Draft glosses + review sheets (reads gloss_overrides.json). -> glosses_review*.tsv
python3 make_gloss_review.py _clean_words.txt

# 8. Merge everything. -> words.json
python3 assemble.py

# 9. Public CSV. -> ../public/spanish-1000-most-common-words.csv
python3 export_download.py
```

## Gloss review

`make_gloss_review.py` picks a draft English gloss per word using the spaCy POS
to choose the right sense, and resolves inflected forms from their lemma. Rows
it can't resolve confidently are flagged in `glosses_review.tsv`
(`Y` = needs attention, `L` = lemma-resolved quick-confirm, blank = confident).

Human review decisions live in **`gloss_overrides.json`** (`word -> gloss`), the
durable source of truth. Editing it and re-running steps 7 and 8 re-applies the
overrides with no rework; regenerating the review sheets never clobbers them.

## Pronunciation notes

Latin American Spanish (seseo, yeismo). Trill `/r/` word-initially and after
`n`/`l`/`s`; tap `/ɾ/` elsewhere. Word-final `-y` becomes the glide `/i̯/`.
Intervocalic `b`/`d`/`g` are kept as stops on purpose (clearer for learners).

## License

Derived data inherits CC BY-SA 4.0 from the source corpus and Wiktionary.
Attribution: Hermit Dave FrequencyWords / OpenSubtitles; Wiktionary contributors.
