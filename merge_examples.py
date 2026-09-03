"""
Fusiona els exemples extrets de totes les plataformes disponibles
(WhatsApp, Instagram, Discord...) en un únic all_extracted_examples.py,
llest per passar per filter_examples.py.

Detecta automàticament quins fitxers de plataforma existeixen — no cal
tenir-los tots. Simplement executa aquest script després d'haver corregut
els extractors de les plataformes que facis servir.

Ús:
    python3 merge_examples.py
"""

from pathlib import Path

all_pairs = []

# Cada entrada: (nom del mòdul sense .py, nom de la variable dins, etiqueta)
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

    # Dedup global (per si el mateix missatge apareix duplicat entre fonts)
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