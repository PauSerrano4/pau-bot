"""
Extract and process ALL exported WhatsApp chats (.zip) in a folder,
combining the extracted examples into a single file.

Usage:
    python process_all_chats.py /chats/WhatsApp "El Teu Nom"

What it does:
     1. Finds all .zip files inside the specified folder.
     2. Extracts each one into a temporary folder.
     3. Looks inside each zip for the chat .txt file (usually "_chat.txt" or
         "WhatsApp Chat with X.txt").
     4. Passes each .txt file through extract_whatsapp_examples.py.
     5. Combines all found examples into a single file,
         `all_extracted_examples.py`.

Note: if your name appears differently in different contacts' exports,
you can pass several comma-separated names: "Pau,Pau Serrano,Pau S."
"""

import sys
import zipfile
import tempfile
from pathlib import Path

# Reutilitzem la lògica de parsing ja creada
from extract_whatsapp_examples import parse_chat


def find_zips(folder: Path):
    return sorted(folder.glob("*.zip"))


def find_chat_txt(extracted_dir: Path):
    """A WhatsApp zip usually contains one main .txt file
    (_chat.txt or "WhatsApp Chat with X.txt") plus media. Use the
    largest .txt file when there are several."""
    txts = list(extracted_dir.glob("*.txt"))
    if not txts:
        return None
    return max(txts, key=lambda p: p.stat().st_size)


def main():
    if len(sys.argv) != 3:
        print('Ús: python process_all_chats.py <carpeta_amb_zips> "El Teu Nom[,Nom2,...]"')
        sys.exit(1)

    folder = Path(sys.argv[1])
    my_names = [n.strip() for n in sys.argv[2].split(",")]
    # WhatsApp often replaces your name with "Tú" (or "You" in English
    # exports), even when your profile name is different. Always try these
    # as fallbacks.
    for fallback in ("Tú", "You"):
        if fallback not in my_names:
            my_names.append(fallback)

    if not folder.is_dir():
        print(f"No trobo la carpeta: {folder}")
        sys.exit(1)

    zips = find_zips(folder)
    if not zips:
        print(f"No he trobat cap .zip dins de {folder}")
        sys.exit(1)

    print(f"Trobats {len(zips)} fitxers zip:")
    for z in zips:
        print(f"  - {z.name}")

    all_pairs = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        for zip_path in zips:
            extract_dir = tmp_path / zip_path.stem
            extract_dir.mkdir(parents=True, exist_ok=True)

            try:
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(extract_dir)
            except zipfile.BadZipFile:
                print(f"  [AVÍS] {zip_path.name} no és un zip vàlid, l'ometo")
                continue

            chat_txt = find_chat_txt(extract_dir)
            if not chat_txt:
                print(f"  [AVÍS] No he trobat cap .txt dins de {zip_path.name}")
                continue

            found_for_this_zip = 0
            for name in my_names:
                pairs = parse_chat(str(chat_txt), name)
                if pairs:
                    all_pairs.extend(pairs)
                    found_for_this_zip += len(pairs)
                    break  # ja hem trobat el nom correcte per aquest xat

            print(f"  {zip_path.name}: {found_for_this_zip} exemples extrets")

    # Remove exact duplicates while preserving order.
    seen = set()
    unique_pairs = []
    for received, sent in all_pairs:
        key = (received, sent)
        if key not in seen:
            seen.add(key)
            unique_pairs.append((received, sent))

    out_path = Path("whatsapp_examples.py")
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Exemples extrets automàticament de tots els xats de WhatsApp\n\n")
        f.write("WHATSAPP_EXAMPLES = [\n")
        for received, sent in unique_pairs:
            received_clean = received.replace('"', "'")
            sent_clean = sent.replace('"', "'")
            f.write(f'    {{"input": "{received_clean}", "output": "{sent_clean}"}},\n')
        f.write("]\n")

    print(f"\nTotal: {len(unique_pairs)} exemples únics -> whatsapp_examples.py")
    print(
        "Següent pas: python3 merge_examples.py per combinar-ho amb "
        "altres plataformes (Instagram, Discord) si en tens, o per "
        "generar directament all_extracted_examples.py si només fas "
        "servir WhatsApp."
    )


if __name__ == "__main__":
    main()