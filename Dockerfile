# Lightweight Python base image.
FROM python:3.12-slim

WORKDIR /app

# Minimal system dependencies (required by some ML libraries).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to take advantage of Docker's cache.
COPY requirements.txt .

# Install the CPU-only version of PyTorch (much smaller than the CUDA-enabled
# version; GPU support is unnecessary because embeddings are computed locally).
# This reduces the image size by several GB.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the code.
COPY . .

# Download the embedding model at BUILD TIME, not in response to the first
# user message. This keeps container startup fast and avoids relying on the
# network in production.
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]