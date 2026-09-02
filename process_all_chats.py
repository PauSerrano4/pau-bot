"""
Descomprimeix i processa TOTS els xats de WhatsApp exportats (.zip) d'una
carpeta, i ajunta els exemples extrets en un sol fitxer.

Ús:
    python process_all_chats.py /chats/WhatsApp "El Teu Nom"

Què fa:
    1. Busca tots els .zip dins de la carpeta indicada
    2. Descomprimeix cadascun a una carpeta temporal
    3. Dins de cada zip busca el .txt del xat (normalment "_chat.txt" o
       "WhatsApp Chat with X.txt")
    4. Passa cada .txt pel parser de extract_whatsapp_examples.py
    5. Ajunta tots els exemples trobats a un únic fitxer
       `all_extracted_examples.py`

Nota: si tens xats amb noms de contacte diferents al teu (p.ex. si el teu
nom apareix diferent segons el telèfon de l'altra persona), pots passar
diversos noms separats per comes: "Pau,Pau Serrano,Pau S."
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
    """Dins d'un zip de WhatsApp sol haver-hi un .txt principal
    (_chat.txt o "WhatsApp Chat with X.txt") + multimèdia. Agafem el
    .txt més gran per si hi ha diversos."""
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
    # WhatsApp sovint substitueix el teu propi nom per "Tú" (o "You" en
    # exportacions en anglès) al fitxer exportat, encara que el teu nom
    # de perfil sigui un altre. Ho provem sempre com a fallback.
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

    # Eliminem duplicats exactes mantenint l'ordre
    seen = set()
    unique_pairs = []
    for received, sent in all_pairs:
        key = (received, sent)
        if key not in seen:
            seen.add(key)
            unique_pairs.append((received, sent))

    out_path = Path("all_extracted_examples.py")
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Exemples extrets automàticament de tots els xats — REVISA'LS\n")
        f.write("# Esborra els sensibles, repetitius o poc representatius abans\n")
        f.write("# de copiar-ne una selecció (15-30) a persona_config.py\n\n")
        f.write("ALL_EXTRACTED_EXAMPLES = [\n")
        for received, sent in unique_pairs:
            received_clean = received.replace('"', "'")
            sent_clean = sent.replace('"', "'")
            f.write(f'    {{"input": "{received_clean}", "output": "{sent_clean}"}},\n')
        f.write("]\n")

    print(f"\nTotal: {len(unique_pairs)} exemples únics -> {out_path}")
    print(
        "Següent pas: obre el fitxer, esborra el que no serveixi (temes "
        "sensibles, missatges poc representatius, coses massa curtes com "
        "'ok' o 'jaja'), i copia'n 15-30 de bons a persona_config.py -> "
        "FEW_SHOT_EXAMPLES"
    )


if __name__ == "__main__":
    main()