#!/usr/bin/env python3
"""Stage 3 spike: rule-based Spanish syllabification + stress + IPA (Latin American: seseo, yeismo).
Validates the pronunciation MOAT fields with ZERO heavy dependencies.
Lemma/POS (spaCy) and English gloss (dictionary) are validated separately."""
import sys, unicodedata

VOWELS = set("aeiouáéíóúü")
STRONG = set("aeoáéó")
WEAK = set("iuü")            # unaccented weak
ACCENT = {"á":"a","é":"e","í":"i","ó":"o","ú":"u"}
ACCENTED = set("áéíóú")
# inseparable onset clusters (consonant + liquid) + digraphs
CLUSTERS = {"pr","br","tr","dr","cr","gr","fr","pl","bl","cl","gl","fl"}
DIGRAPHS = {"ch","ll","rr"}

def is_vowel(c): return c in VOWELS

def syllabify(w):
    # NB: input is already lowercased + sentinelized by preprocess(); do NOT lower() here
    # mark vowel groups (diphthong/hiatus)
    # Step 1: split into syllable nuclei by scanning
    chars = list(w)
    n = len(chars)
    # find vowel group boundaries
    def vowel_group(i):
        # returns end index (exclusive) of a vowel cluster starting at i
        j = i
        while j < n and is_vowel(chars[j]):
            j += 1
        return j
    syllables = []
    i = 0
    # We build syllables greedily: onset + nucleus + trailing consonants assigned by rules
    # Simpler approach: split consonants between nuclei.
    # 1) tokenize into segments: sequences of consonants (C) and vowels (V)
    segs = []
    k = 0
    while k < n:
        if is_vowel(chars[k]):
            j = vowel_group(k)
            segs.append(("V", "".join(chars[k:j])))
            k = j
        else:
            j = k
            while j < n and not is_vowel(chars[j]):
                j += 1
            segs.append(("C", "".join(chars[k:j])))
            k = j
    # handle vowel groups: split hiatus (two strong, or accented weak) into separate nuclei
    nuclei = []  # list of vowel-group strings, possibly split
    seg_expand = []
    for typ, s in segs:
        if typ == "C":
            seg_expand.append(("C", s))
        else:
            # split vowel string into syllable nuclei
            parts = split_vowels(s)
            for idx, p in enumerate(parts):
                seg_expand.append(("V", p))
    segs = seg_expand
    # Now assign consonants. Build syllables around each V.
    result = []
    idx = 0
    m = len(segs)
    # leading consonant onset
    cur = ""
    # We'll iterate: [C?] V, then distribute following C cluster between this and next V
    pos = 0
    # collect indices of V segments
    while pos < m:
        typ, s = segs[pos]
        if typ == "C":
            cur += s
            pos += 1
            continue
        # s is a vowel nucleus
        cur += s
        # look ahead: consonants until next vowel
        cpos = pos + 1
        cons = ""
        while cpos < m and segs[cpos][0] == "C":
            cons += segs[cpos][1]
            cpos += 1
        has_next_vowel = cpos < m
        if not has_next_vowel:
            cur += cons
            result.append(cur); cur = ""
            break
        # distribute cons between cur syllable (coda) and next syllable (onset)
        coda, onset = distribute(cons)
        cur += coda
        result.append(cur)
        cur = onset
        pos = cpos
    if cur:
        result.append(cur)
    return [r for r in result if r]

def split_vowels(s):
    """Split a vowel sequence into nuclei (diphthongs stay, hiatus splits)."""
    if len(s) == 1:
        return [s]
    out = []
    i = 0
    while i < len(s):
        if i + 1 < len(s):
            a, b = s[i], s[i+1]
            a_strong = a in "aeoáéó"; b_strong = b in "aeoáéó"
            a_acc = a in ACCENTED; b_acc = b in ACCENTED
            # accented weak vowel -> hiatus
            if (a in "íú") or (b in "íú"):
                out.append(a); i += 1; continue
            # two strong -> hiatus
            if a_strong and b_strong:
                out.append(a); i += 1; continue
            # otherwise diphthong (weak+strong, strong+weak, weak+weak)
            # check triphthong weak-strong-weak
            if i + 2 < len(s) and (s[i] in "iuü") and (s[i+1] in "aeoáéó") and (s[i+2] in "iuü"):
                out.append(s[i:i+3]); i += 3; continue
            out.append(s[i:i+2]); i += 2; continue
        else:
            out.append(s[i]); i += 1
    return out

def distribute(cons):
    """Return (coda_for_prev, onset_for_next) for a consonant cluster between vowels."""
    L = len(cons)
    if L == 0:
        return "", ""
    if L == 1:
        return "", cons                       # V-CV
    low = cons.lower()
    if L == 2:
        if low in DIGRAPHS or low in CLUSTERS:
            return "", cons                    # inseparable -> onset
        return cons[0], cons[1]                # VC-CV
    # L >= 3: try to keep last-two as valid onset
    last2 = low[-2:]
    if last2 in DIGRAPHS or last2 in CLUSTERS:
        return cons[:-2], cons[-2:]
    return cons[:-1], cons[-1]

def stressed_index(syls):
    """Return index of stressed syllable."""
    # written accent wins
    for i, s in enumerate(syls):
        if any(ch in ACCENTED for ch in s):
            return i
    if len(syls) == 1:
        return 0
    # get last letter of the word
    word = "".join(syls)
    last = word[-1]
    if last in "aeiouns" or last in "áéíóú":
        return len(syls) - 2   # llana (penultimate)
    return len(syls) - 1       # aguda (last)

def to_ipa(syls, stress_i):
    """Broad Latin American IPA (seseo, yeismo). Approximate."""
    out = []
    for si, syl in enumerate(syls):
        ipa = transcribe_syllable(syl)
        if si == stress_i:
            ipa = "ˈ" + ipa
        out.append(ipa)
    return "/" + "".join(out) + "/"

def transcribe_syllable(s):
    res = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        nxt = s[i+1] if i+1 < n else ""
        pair = c + nxt
        if c == "K": res.append("k"); i += 1; continue   # sentinel from 'qu'
        if c == "G": res.append("ɡ"); i += 1; continue   # sentinel from 'gu'+e/i
        if c == "R": res.append("r"); i += 1; continue   # trill: word-initial / after n,l,s
        if c == "Y": res.append("i̯"); i += 1; continue  # word-final glide /i̯/
        if pair == "ch": res.append("tʃ"); i += 2; continue
        if pair == "ll": res.append("ʝ"); i += 2; continue
        if pair == "rr": res.append("r"); i += 2; continue
        if pair == "qu" and nxt == "u": pass
        if c == "q" and nxt == "u": res.append("k"); i += 2; continue
        if c == "g" and nxt == "u" and (i+2 < n and s[i+2] in "eéií"):
            res.append("ɡ"); i += 2; continue  # gue/gui -> u silent
        if c == "c":
            # soft before front vowels, accented or not (policía, hacía)
            if nxt in "eéií": res.append("s"); i += 1; continue  # seseo
            res.append("k"); i += 1; continue
        if c == "z": res.append("s"); i += 1; continue          # seseo
        if c == "g":
            if nxt in "eéií": res.append("x"); i += 1; continue
            res.append("ɡ"); i += 1; continue
        if c == "j": res.append("x"); i += 1; continue
        if c == "ñ": res.append("ɲ"); i += 1; continue
        if c == "h": i += 1; continue                            # silent
        if c == "v": res.append("b"); i += 1; continue
        if c == "y":
            if s == "y" or (n == 1): res.append("i"); i += 1; continue
            res.append("ʝ"); i += 1; continue
        if c == "x": res.append("ks"); i += 1; continue
        if c == "r": res.append("ɾ"); i += 1; continue           # single r (approx)
        if c == "w": res.append("w"); i += 1; continue
        if c in ACCENT: res.append(ACCENT[c]); i += 1; continue
        if c == "ü": res.append("u"); i += 1; continue
        res.append(c); i += 1
    return "".join(res)

import re
def preprocess(w):
    """Collapse silent-u digraphs to consonant sentinels so 'u' isn't a nucleus.
    K = /k/ (from qu), G = /ɡ/ (from gu before e/i)."""
    w = w.lower()
    w = w.replace("qu", "K")
    w = re.sub(r"gu([eéií])", r"G\1", w)
    return w

def mark_context(w):
    """Word-position phonetic marks the per-syllable transcriber can't see.
    Runs after preprocess() so K/G sentinels are already in place.
    R = trill /r/ (word-initial or after n,l,s); Y = word-final glide /i̯/."""
    chars = list(w)
    n = len(chars)
    for i, c in enumerate(chars):
        if c != "r":
            continue
        prev = chars[i - 1] if i > 0 else ""
        nxt = chars[i + 1] if i + 1 < n else ""
        if prev == "r" or nxt == "r":
            continue                      # part of 'rr' digraph -> trill handled in transcribe
        if i == 0 or prev in ("n", "l", "s"):
            chars[i] = "R"                # trill
    if n > 1 and chars[-1] == "y":
        chars[-1] = "Y"                   # word-final glide
    return "".join(chars)

def enrich(word):
    pw = mark_context(preprocess(word))
    syls = syllabify(pw)
    si = stressed_index(syls)
    ipa = to_ipa(syls, si)
    # restore display spelling for syllables (sentinels back to source letters)
    def restore(s):
        return s.replace("K", "qu").replace("G", "gu").replace("R", "r").replace("Y", "y")
    disp = restore("-".join(syls))
    stress_syl = restore(syls[si]) if syls else word
    return disp, stress_syl, ipa

def enrich_record(rank, word, count=None):
    disp, stress_syl, ipa = enrich(word)
    return {
        "rank": rank, "word": word, "count": count,
        "syllables": disp, "stress": stress_syl, "ipa": ipa,
        # TODO (pipeline): lemma, pos (spaCy), gloss (dictionary + review), coverage
    }

if __name__ == "__main__":
    # Usage: python enrich.py es_50k.txt [limit]  ->  JSON array of enriched rows on stdout
    import json
    path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    rows = []
    with open(path) as f:
        for rank, line in enumerate(f, 1):
            if rank > limit:
                break
            parts = line.split()
            if len(parts) < 1:
                continue
            word = parts[0]
            count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            rows.append(enrich_record(rank, word, count))
    print(json.dumps(rows, ensure_ascii=False, indent=2))
