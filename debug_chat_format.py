"""
Print the first lines of the .txt file inside a WhatsApp zip as raw text
so you can inspect its exact format (useful for debugging the parser when
it does not detect any messages).

Usage:
    python3 debug_chat_format.py "chats/WhatsApp/Aleix Truzman.zip"
"""

import sys
import zipfile
import tempfile
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print('Ús: python3 debug_chat_format.py "ruta/al/xat.zip"')
        sys.exit(1)

    zip_path = Path(sys.argv[1])

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp_path)

        txts = list(tmp_path.glob("*.txt"))
        if not txts:
            print("No .txt file found inside the zip")
            sys.exit(1)

        chat_txt = max(txts, key=lambda p: p.stat().st_size)
        print(f"Fitxer trobat: {chat_txt.name}\n")

        with chat_txt.open("r", encoding="utf-8") as f:
            lines = [next(f, "") for _ in range(15)]

        print("First 15 lines (using repr() to reveal hidden characters):\n")
        for i, line in enumerate(lines):
            print(f"{i}: {repr(line)}")


if __name__ == "__main__":
    main()