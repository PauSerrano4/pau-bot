"""
Merge examples extracted from all available platforms
(WhatsApp, Instagram, Discord...) into a single all_extracted_examples.py
file ready for filter_examples.py.

Automatically detects which platform files exist; you do not need all of
them. Run this script after running the extractors for the platforms you use.

Usage:
    python3 merge_examples.py
"""

from pathlib import Path

all_pairs = []

# Each entry: (module name without .py, variable name, label)
SOURCES = [
    ("whatsapp_examples", "WHATSAPP_EXAMPLES", "WhatsApp"),
    ("instagram_examples", "INSTAGRAM_EXAMPLES", "Instagram"),
    ("discord_examples", "DISCORD_EXAMPLES", "Discord"),
]


def main():
    for module_name, var_name, label in SOURCES:
        if not Path(f"{module_name}.py").exists():
            print(f"[omès] {label}: no s'ha trobat {module_name}.py")
            continue
        module = __import__(module_name)
        examples = getattr(module, var_name)
        pairs = [(ex["input"], ex["output"]) for ex in examples]
        print(f"[inclòs] {label}: {len(pairs)} exemples")
        all_pairs.extend(pairs)

    if not all_pairs:
        print("\nNo s'ha trobat cap fitxer d'exemples. Executa primer algun "
              "dels extractors (process_all_chats.py, "
              "extract_instagram_examples.py, etc.)")
        return

    # Global deduplication (in case the same message appears in multiple sources).
    seen = set()
    unique_pairs = []
    for received, sent in all_pairs:
        key = (received, sent)
        if key not in seen:
            seen.add(key)
            unique_pairs.append((received, sent))

    out_path = Path("all_extracted_examples.py")
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Exemples fusionats de totes les plataformes — REVISA'LS\n")
        f.write("# Esborra els sensibles, repetitius o poc representatius abans\n")
        f.write("# de continuar amb filter_examples.py\n\n")
        f.write("ALL_EXTRACTED_EXAMPLES = [\n")
        for received, sent in unique_pairs:
            r = received.replace('"', "'")
            s = sent.replace('"', "'")
            f.write(f'    {{"input": "{r}", "output": "{s}"}},\n')
        f.write("]\n")

    print(f"\nTotal fusionat: {len(unique_pairs)} exemples únics -> {out_path}")
    print("Següent pas: python3 filter_examples.py")


if __name__ == "__main__":
    main()