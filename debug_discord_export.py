"""
Discord does not have a simple "chat export" like WhatsApp; you need to
request your data:
    Discord > User Settings > Privacy & Safety >
    "Request all of my data" (it can take hours or days to arrive by email)

L'estructura sol ser:
    package/messages/index.json          (mapa canal_id -> nom del canal)
    package/messages/c<canal_id>/messages.csv

Usage for this script (inspection only; it does not extract anything yet):
    python3 debug_discord_export.py "package/messages"

Shows the real structure to confirm whether the CSV contains only YOUR
messages or also the other person's (Discord has changed this behavior
several times), which is necessary to determine whether question/reply
pairs can be built.
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

    # Use the first channel with data to inspect the CSV.
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