"""
Discord no té una "exportació de xat" senzilla com WhatsApp — cal
sol·licitar les teves dades:
    Discord > Configuració d'usuari > Privadesa i seguretat >
    "Sol·licita totes les meves dades" (triga entre hores i dies a
    arribar per correu)

L'estructura sol ser:
    package/messages/index.json          (mapa canal_id -> nom del canal)
    package/messages/c<canal_id>/messages.csv

Ús d'aquest script (només per inspeccionar, no extreu res encara):
    python3 debug_discord_export.py "package/messages"

Mostra l'estructura real per confirmar si el CSV inclou només els TEUS
missatges o també els de l'altra persona (Discord ha canviat aquest
comportament diverses vegades) — necessari per saber si podem construir
parelles pregunta/resposta o no.
"""

import csv
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print('Ús: python3 debug_discord_export.py "package/messages"')
        sys.exit(1)

    messages_dir = Path(sys.argv[1])
    index_path = messages_dir / "index.json"

    if not index_path.exists():
        print(f"No trobo index.json a {messages_dir}")
        print("Comprova que la ruta apunti a la carpeta 'messages' del paquet.")
        sys.exit(1)

    with index_path.open("r", encoding="utf-8") as f:
        index = json.load(f)

    print(f"Trobats {len(index)} canals a index.json. Primers 5:")
    for i, (channel_id, name) in enumerate(index.items()):
        if i >= 5:
            break
        print(f"  {channel_id}: {name}")

    # Agafem el primer canal amb dades per inspeccionar el CSV
    for channel_id in index:
        csv_path = messages_dir / f"c{channel_id}" / "messages.csv"
        if csv_path.exists():
            print(f"\nInspeccionant: {csv_path}")
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                print(f"Columnes: {header}")
                print("\nPrimeres 10 files:")
                for i, row in enumerate(reader):
                    if i >= 10:
                        break
                    print(f"  {row}")
            break
    else:
        print("No he trobat cap messages.csv dins les carpetes de canal.")


if __name__ == "__main__":
    main()