"""
Extract examples (received question -> your reply pairs) from an
Instagram conversation export.

How to get the export:
    Instagram > Settings > Accounts Center > Your information and
    permissions > Download your information > select "Messages" >
    JSON format (NOT HTML; the parser expects JSON)

Typical structure after extraction:
    your_instagram_activity/messages/inbox/<conversation_name>_<id>/message_1.json
    (very long conversations may also contain message_2.json, etc.)

Usage:
    python3 extract_instagram_examples.py "your_instagram_activity/messages/inbox" "Your Instagram name"

Generates instagram_examples.py with INSTAGRAM_EXAMPLES.
"""

import json
import sys
from pathlib import Path


def fix_encoding(text: str) -> str:
    """Fix a known encoding bug in Meta's JSON exports: non-ASCII
    characters (accents, emojis) can be misinterpreted.
    This is the standard fix for recovering the correct text."""
    try:
        return text.encode("latin1").decode("utf8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def parse_conversation_folder(folder: Path, my_name: str):
    """Read all message_N.json files in a conversation folder and
    return pairs (received message, your reply)."""
    json_files = sorted(folder.glob("message_*.json"))
    if not json_files:
        return []

    all_messages = []
    for jf in json_files:
        with jf.open("r", encoding="utf-8") as f:
            data = json.load(f)
        all_messages.extend(data.get("messages", []))

    # Instagram exports messages from newest to oldest, so reverse them.
    all_messages.sort(key=lambda m: m.get("timestamp_ms", 0))

    pairs = []
    for i in range(len(all_messages) - 1):
        msg = all_messages[i]
        next_msg = all_messages[i + 1]

        sender = fix_encoding(msg.get("sender_name", ""))
        next_sender = fix_encoding(next_msg.get("sender_name", ""))
        content = msg.get("content")
        next_content = next_msg.get("content")

        if not content or not next_content:
            continue  # Messages containing only a sticker/photo have no text.

        if sender != my_name and next_sender == my_name:
            pairs.append((fix_encoding(content), fix_encoding(next_content)))

    return pairs


def main():
    if len(sys.argv) != 3:
        print('Ús: python3 extract_instagram_examples.py "<carpeta inbox>" "El teu nom"')
        sys.exit(1)

    inbox_path = Path(sys.argv[1])
    my_name = sys.argv[2]

    if not inbox_path.is_dir():
        print(f"No trobo la carpeta: {inbox_path}")
        sys.exit(1)

    conversation_folders = [p for p in inbox_path.iterdir() if p.is_dir()]
    print(f"Trobades {len(conversation_folders)} converses")

    all_pairs = []
    for folder in conversation_folders:
        pairs = parse_conversation_folder(folder, my_name)
        if pairs:
            print(f"  {folder.name}: {len(pairs)} exemples")
            all_pairs.extend(pairs)

    # Dedup
    seen = set()
    unique_pairs = []
    for received, sent in all_pairs:
        key = (received, sent)
        if key not in seen:
            seen.add(key)
            unique_pairs.append((received, sent))

    out_path = Path("instagram_examples.py")
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Exemples extrets d'Instagram — REVISA'LS abans de fer servir\n\n")
        f.write("INSTAGRAM_EXAMPLES = [\n")
        for received, sent in unique_pairs:
            r = received.replace('"', "'").replace("\n", " ")
            s = sent.replace('"', "'").replace("\n", " ")
            f.write(f'    {{"input": "{r}", "output": "{s}"}},\n')
        f.write("]\n")

    print(f"\nTotal: {len(unique_pairs)} exemples únics -> instagram_examples.py")


if __name__ == "__main__":
    main()