"""
Filtra els exemples extrets (all_extracted_examples.py) eliminant soroll:
respostes massa curtes, purament fàtiques ("ok", "jaja"), o buides de
contingut. Deixa un corpus net per indexar amb build_style_index.py.

Ús:
    python3 filter_examples.py
    (llegeix all_extracted_examples.py, escriu filtered_examples.py)
"""

import re
from all_extracted_examples import ALL_EXTRACTED_EXAMPLES

# Respostes purament fàtiques que no aporten res com a exemple d'estil
FILLER_ONLY = {
    "ok", "okey", "oki", "okay", "vale", "val", "va", "si", "sí", "no",
    "jaja", "jajaja", "jajajaja", "jeje", "jejeje", "xD", "xd", "haha",
    "hahaha", "ns", "nse", "clar", "exacte", "ya", "yep", "yes", "nop",
    "bueno", "true", "cert", "d'acord", "dacord", "😂", "👍", "❤️",
}

MIN_CHARS_INPUT = 8    # el context ha de tenir prou substància
MIN_CHARS_OUTPUT = 6   # la resposta ha d'aportar alguna cosa


def normalize(text: str) -> str:
    return re.sub(r"[^\w\sàèéíòóúïüçñ]", "", text.strip().lower())


def is_low_value(input_text: str, output_text: str) -> bool:
    if len(input_text) < MIN_CHARS_INPUT or len(output_text) < MIN_CHARS_OUTPUT:
        return True
    if normalize(output_text) in FILLER_ONLY:
        return True
    if normalize(input_text) in FILLER_ONLY:
        return True
    # missatges que són només emojis/puntuació
    if not re.search(r"\w", output_text):
        return True
    return False


def main():
    kept = []
    dropped = 0

    for ex in ALL_EXTRACTED_EXAMPLES:
        if is_low_value(ex["input"], ex["output"]):
            dropped += 1
            continue
        kept.append(ex)

    print(f"Originals: {len(ALL_EXTRACTED_EXAMPLES)}")
    print(f"Descartats (soroll): {dropped}")
    print(f"Restants: {len(kept)}")

    with open("filtered_examples.py", "w", encoding="utf-8") as f:
        f.write("# Exemples filtrats — encara val la pena una ullada ràpida\n")
        f.write("# abans d'indexar-los, per si hi ha temes molt sensibles\n")
        f.write("# que prefereixis excloure manualment.\n\n")
        f.write("FILTERED_EXAMPLES = [\n")
        for ex in kept:
            inp = ex["input"].replace('"', "'")
            out = ex["output"].replace('"', "'")
            f.write(f'    {{"input": "{inp}", "output": "{out}"}},\n')
        f.write("]\n")

    print("-> filtered_examples.py")


if __name__ == "__main__":
    main()