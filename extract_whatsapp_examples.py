"""
Ajuda a convertir una exportació de xat de WhatsApp en exemples few-shot
per a persona_config.py.

Ús:
    python extract_whatsapp_examples.py xat_exportat.txt "El Teu Nom"

Genera un fitxer `extracted_examples.py` amb parelles (missatge rebut,
la teva resposta) llestes per copiar dins FEW_SHOT_EXAMPLES.

Nota: el format d'exportació de WhatsApp pot variar lleugerament segons
el sistema operatiu i idioma del telèfon. Si el parsing falla, revisa
el patró REGEX_LINE i ajusta'l al format real del teu fitxer.
"""

import re
import sys
from pathlib import Path

# Dos formats habituals d'exportació de WhatsApp:
# Android/antic:  "12/8/25, 10:32 - Nom: Missatge"
# iPhone/nou:     "[12/13/25, 11:19:56 PM] Nom: Missatge"
REGEX_LINE_DASH = re.compile(
    r"^\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}\s*-\s*([^:]+):\s*(.*)$"
)
REGEX_LINE_BRACKET = re.compile(
    r"^\[\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|a\.\s?m\.|p\.\s?m\.)?\]\s*([^:]+):\s*(.*)$"
)


def parse_chat(filepath: str, my_name: str):
    lines = Path(filepath).read_text(encoding="utf-8").splitlines()

    messages = []  # (autor, text)
    for line in lines:
        # elimina marques de direcció de text invisibles que WhatsApp
        # a vegades afegeix (U+200E, U+200F)
        clean_line = line.lstrip("\u200e\u200f")

        match = REGEX_LINE_BRACKET.match(clean_line) or REGEX_LINE_DASH.match(clean_line)
        if match:
            author, text = match.groups()
            messages.append((author.strip(), text.strip()))
        elif messages:
            # línia de continuació d'un missatge multilínia
            author, text = messages[-1]
            messages[-1] = (author, text + " " + line.strip())

    # Construir parelles: missatge d'algú altre seguit d'una resposta teva
    pairs = []
    for i in range(len(messages) - 1):
        author, text = messages[i]
        next_author, next_text = messages[i + 1]
        if author != my_name and next_author == my_name:
            if text and next_text and "<Multimedia omès>" not in text:
                pairs.append((text, next_text))

    return pairs


def main():
    if len(sys.argv) != 3:
        print('Ús: python extract_whatsapp_examples.py <fitxer.txt> "El Teu Nom"')
        sys.exit(1)

    filepath, my_name = sys.argv[1], sys.argv[2]
    pairs = parse_chat(filepath, my_name)

    out_path = Path("extracted_examples.py")
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Exemples extrets automàticament — revisa'ls abans d'usar-los\n")
        f.write("# Elimina qualsevol dada sensible o poc representativa\n\n")
        f.write("EXTRACTED_EXAMPLES = [\n")
        for received, sent in pairs:
            received_clean = received.replace('"', "'")
            sent_clean = sent.replace('"', "'")
            f.write(f'    {{"input": "{received_clean}", "output": "{sent_clean}"}},\n')
        f.write("]\n")

    print(f"Extrets {len(pairs)} exemples -> {out_path}")
    print("Revisa'ls, esborra els irrellevants/sensibles, i copia'n els millors "
          "(15-30 variats) a persona_config.py -> FEW_SHOT_EXAMPLES")


if __name__ == "__main__":
    main()