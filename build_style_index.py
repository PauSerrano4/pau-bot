"""
Construeix un índex d'embeddings locals dels exemples filtrats, perquè
després es puguin recuperar dinàmicament els exemples més semblants a
cada missatge nou (RAG aplicat a l'estil, no al coneixement).

Fa servir sentence-transformers (model local, sense necessitat de cap
API key ni cost per token).

Ús:
    pip install sentence-transformers numpy
    python3 build_style_index.py
    (llegeix filtered_examples.py, escriu style_index.pkl)
"""

import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

from filtered_examples import FILTERED_EXAMPLES

# Model multilingüe petit i ràpid, va bé per català/castellà/anglès
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def main():
    print(f"Carregant model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    inputs = [ex["input"] for ex in FILTERED_EXAMPLES]
    print(f"Generant embeddings per {len(inputs)} exemples...")

    embeddings = model.encode(
        inputs, show_progress_bar=True, convert_to_numpy=True
    )

    with open("style_index.pkl", "wb") as f:
        pickle.dump(
            {
                "examples": FILTERED_EXAMPLES,
                "embeddings": embeddings,
                "model_name": MODEL_NAME,
            },
            f,
        )

    print(f"Índex desat -> style_index.pkl ({len(inputs)} exemples)")


if __name__ == "__main__":
    main()