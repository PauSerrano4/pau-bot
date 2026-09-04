"""
Style-example retrieval: given a new message, find the K most similar
examples in the corpus (by embedding) and inject them into the system
prompt as dynamic few-shot examples.

Requires build_style_index.py to have been run first.
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
    """Return the k most similar examples (dicts with 'input'/'output')
    for `query`, ordered from most to least similar."""
    examples, embeddings, model = _load_index()

    query_emb = model.encode([query], convert_to_numpy=True)[0]

    # Cosine similarity.
    norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_emb)
    norms[norms == 0] = 1e-10
    similarities = (embeddings @ query_emb) / norms

    top_k_idx = np.argsort(similarities)[::-1][:k]
    return [examples[i] for i in top_k_idx]


def index_available() -> bool:
    import os

    return os.path.exists(INDEX_PATH)