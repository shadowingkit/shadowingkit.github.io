#!/usr/bin/env python3
"""Regression guard for the rule-based enrichment.

Hand-verified Latin American Spanish (seseo, yeismo). Locks the pronunciation
MOAT fields before scaling to the full top-1000. Run standalone:

    python3 test_enrich.py

Conventions used here (deliberate):
- Trill /r/ word-initially and after n, l, s (and the 'rr' digraph). Tap /ɾ/ elsewhere.
- Word-final -y -> glide /i̯/ (muy, hay, estoy). Non-final 'y' -> /ʝ/ (yeismo).
- Intervocalic b/d/g kept as stops /b d ɡ/ on purpose (clearer for learners).
- No hiatus dots in IPA (cosmetic, skipped): día -> /ˈdia/.
- Monosyllables carry a stress mark (broad per-word transcription).
"""
import sys
from enrich import enrich

# word -> expected IPA. Hand-verified.
CASES = {
    # controls / basics
    "que":        "/ˈke/",
    "de":         "/ˈde/",
    "hola":       "/ˈola/",     # h silent
    "gente":      "/ˈxente/",   # g before e -> x
    "joven":      "/ˈxoben/",   # j -> x, v -> b
    "año":        "/ˈaɲo/",     # ñ -> ɲ
    "niño":       "/ˈniɲo/",
    "mujer":      "/muˈxeɾ/",   # tap final r
    # tap r (intervocalic / cluster / coda)
    "pero":       "/ˈpeɾo/",
    "caro":       "/ˈkaɾo/",
    "corazón":    "/koɾaˈson/", # z -> s (seseo)
    "seguir":     "/seˈɡiɾ/",   # gu+i silent u
    "otro":       "/ˈotɾo/",    # tr cluster -> tap
    "comer":      "/koˈmeɾ/",
    # trill r (word-initial, rr, and after n/l/s)
    "rojo":       "/ˈroxo/",    # word-initial trill
    "rey":        "/ˈrei̯/",     # trill + final-y glide
    "perro":      "/ˈpero/",    # rr digraph -> trill
    "guerra":     "/ˈɡera/",
    "honra":      "/ˈonra/",    # trill after n
    "alrededor":  "/alredeˈdoɾ/", # trill after l, tap final
    "israel":     "/israˈel/",  # trill after s
    # word-final -y -> glide
    "muy":        "/ˈmui̯/",
    "hay":        "/ˈai̯/",
    "estoy":      "/esˈtoi̯/",
    "hoy":        "/ˈoi̯/",
    "voy":        "/ˈboi̯/",
    "soy":        "/ˈsoi̯/",
    "ley":        "/ˈlei̯/",
    # written accent / hiatus
    "país":       "/paˈis/",
    "día":        "/ˈdia/",
    # soft c/g before ACCENTED front vowels (regression: was /k/, /ɡ/)
    "policía":    "/poliˈsia/",
    "hacía":      "/aˈsia/",
    "decía":      "/deˈsia/",
}


def run():
    failures = []
    for word, expected in CASES.items():
        _, _, ipa = enrich(word)
        status = "ok " if ipa == expected else "FAIL"
        if ipa != expected:
            failures.append((word, expected, ipa))
        print(f"  {status}  {word:<12} {ipa}")
    print()
    if failures:
        print(f"{len(failures)} / {len(CASES)} failed:")
        for word, expected, got in failures:
            print(f"  {word:<12} expected {expected}  got {got}")
        return 1
    print(f"all {len(CASES)} passed")
    return 0


def test_enrich():  # pytest entrypoint
    failures = [w for w, exp in CASES.items() if enrich(w)[2] != exp]
    assert not failures, failures


if __name__ == "__main__":
    sys.exit(run())
