"""
Build a local embedding index of the filtered examples so the most similar
examples can later be retrieved dynamically for each new message (RAG
applied to style, not knowledge).

Uses sentence-transformers (a local model, with no API key or per-token cost).

Usage:
    pip install sentence-transformers numpy
    python3 build_style_index.py
    (llegeix filtered_examples.py, escriu style_index.pkl)
"""

import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

from filtered_examples import FILTERED_EXAMPLES

# Small, fast multilingual model that works well for Catalan/Spanish/English.
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