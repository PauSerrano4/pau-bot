# Imatge base lleugera amb Python
FROM python:3.12-slim

WORKDIR /app

# Dependències del sistema mínimes (algunes llibreries de ML les necessiten)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiem primer només requirements per aprofitar la cache de Docker
COPY requirements.txt .

# Instal·lem PyTorch en versió NOMÉS CPU (molt més petita que la versió
# amb suport CUDA — no la necessitem, ja que els embeddings es calculen
# en local sense GPU). Aquest pas redueix la mida de la imatge en uns
# quants GB.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Ara copiem la resta del codi
COPY . .

# Pre-descarreguem el model d'embeddings EN TEMPS DE BUILD, no en el
# primer missatge de l'usuari — així l'arrencada del contenidor és
# ràpida i no depèn de la xarxa en producció.
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]