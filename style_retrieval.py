"""
Retrieval d'exemples per estil: donat un missatge nou, troba els K
exemples del corpus més semblants (per embedding) per injectar-los
com a few-shot dinàmic al system prompt.

Requereix haver executat prèviament build_style_index.py.
"""

import pickle
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "style_index.pkl"


@lru_cache(maxsize=1)
def _load_index():
    with open(INDEX_PATH, "rb") as f:
        data = pickle.load(f)
    model = SentenceTransformer(data["model_name"])
    return data["examples"], data["embeddings"], model


def get_similar_examples(query: str, k: int = 8):
    """Retorna els k exemples (dicts amb 'input'/'output') més semblants
    al missatge `query`, ordenats de més a menys similars."""
    examples, embeddings, model = _load_index()

    query_emb = model.encode([query], convert_to_numpy=True)[0]

    # similitud del cosinus
    norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_emb)
    norms[norms == 0] = 1e-10
    similarities = (embeddings @ query_emb) / norms

    top_k_idx = np.argsort(similarities)[::-1][:k]
    return [examples[i] for i in top_k_idx]


def index_available() -> bool:
    import os

    return os.path.exists(INDEX_PATH)