# Pau-bot — chatbot que imita el teu estil

## Estructura

- `persona_config.py` — construeix el system prompt: estil + exemples
  (estàtics o via retrieval dinàmic si hi ha índex).
- `app.py` — interfície de xat amb Streamlit connectada a l'API de Claude.
- `process_all_chats.py` — descomprimeix i parseja tots els zips de
  WhatsApp d'una carpeta.
- `extract_whatsapp_examples.py` — parser d'un xat individual (usat pel
  script anterior).
- `debug_chat_format.py` — mostra el format en cru d'un xat per depurar.
- `filter_examples.py` — neteja soroll (respostes fàtiques, massa curtes)
  del corpus extret.
- `build_style_index.py` — genera embeddings dels exemples filtrats.
- `style_retrieval.py` — recupera els exemples més similars a un missatge
  donat, en temps real.
- `requirements.txt` — dependències.

## Pipeline complet (quan tens molts xats exportats, com el teu cas amb 4k+ exemples)

### 1. Instal·la les dependències
```bash
pip install -r requirements.txt
```

### 2. Extreu els exemples de tots els xats
```bash
python3 process_all_chats.py chats/WhatsApp "Pau"
```
Genera `all_extracted_examples.py`.

### 3. Filtra el soroll
```bash
python3 filter_examples.py
```
Elimina respostes tipus "ok", "jaja", massa curtes, etc. Genera
`filtered_examples.py`. Val la pena fer-hi una ullada ràpida per si vols
excloure algun xat sencer per temes sensibles (p.ex. converses familiars).

### 4. Construeix l'índex d'estil
```bash
python3 build_style_index.py
```
Genera embeddings locals (sense API key, model descarregat automàticament
la primera vegada) i els desa a `style_index.pkl`.

Amb aquest índex, **ja no cal seleccionar manualment 15-30 exemples**: el
bot recupera dinàmicament els 8 exemples més semblants a cada missatge nou.
Si prefereixes un enfocament més simple (menys exemples però fixos),
pots ometre els passos 3-4 i omplir `FEW_SHOT_EXAMPLES` a mà a
`persona_config.py` — el codi cau automàticament a aquest fallback si no
troba `style_index.pkl`.

### 5. Configura la clau API (gratuïta) i executa
```bash
pip uninstall -y google-generativeai   # si l'havies instal·lat abans
export GEMINI_API_KEY="la-teva-clau"
streamlit run app.py
```
La clau és gratuïta: la crees a https://aistudio.google.com/apikey amb el
teu compte de Google. Fa servir el nou SDK `google-genai` (l'antic
`google-generativeai` està deprecat) amb el model `gemini-3.7-flash`
dins de la capa gratuïta (límits de peticions per minut/dia, sense
targeta de pagament). Si en el futur dona error de "model not found",
els noms de models de Google canvien sovint — consulta
https://ai.google.dev/gemini-api/docs/models per l'alternativa vigent.

## Iterar i millorar

- Si alguna resposta "no sona a tu", pots ampliar `STYLE_DESCRIPTION` a
  `persona_config.py` amb el tret concret que falta (to, expressions,
  longitud...).
- Si vols ajustar quants exemples es recuperen per missatge, canvia `k=8`
  a la crida `get_similar_examples` dins `persona_config.py`.
- Si vols que recordi fets concrets sobre tu (no només estil), el següent
  pas natural és afegir RAG de coneixement (no només d'estil) amb
  pgvector, ja que fas servir PostgreSQL — puc ajudar-te a muntar-ho quan
  vulguis.

## Notes

- Model per defecte: `gemini-3.7-flash` (Google AI Studio, capa gratuïta —
  sense targeta de pagament, amb límits de peticions per minut/dia que
  per a ús personal van sobrats). Google canvia noms de models sovint;
  si dona error, revisa quin és el vigent.
- L'enfocament de retrieval dinàmic escala molt millor que el few-shot
  estàtic quan tens milers d'exemples: en lloc de triar-ne 20 a mà i
  descartar la resta, cada missatge aprofita automàticament els exemples
  més rellevants de tot el corpus.


## Containerització amb Docker

```bash
docker build -t pau-bot .
docker run -p 8501:8501 -e GEMINI_API_KEY="la-teva-clau" pau-bot
```

Obre http://localhost:8501. La imatge instal·la PyTorch en versió
només-CPU (molt més lleugera) i pre-descarrega el model d'embeddings
en temps de build, així l'arrencada del contenidor és ràpida.

## Pujar-ho a GitHub

```bash
git init
git add .
git commit -m "Primera versió del Pau-bot"
git remote add origin https://github.com/<el-teu-usuari>/pau-bot.git
git push -u origin main
```

**Important:** el `.gitignore` ja exclou el `venv/`, la clau API, i totes
les dades derivades dels xats de WhatsApp (`chats/`, `all_extracted_examples.py`,
`filtered_examples.py`, `style_index.pkl`) — aquests fitxers contenen
converses reals d'altres persones i no s'han de publicar en un
repositori públic. Si vols que qui cloni el repo pugui generar el seu
propi corpus, deixa'ls fora (com ja està configurat); si vols distribuir
el teu índex ja fet, hauràs de treure'l explícitament del `.gitignore` i
assegurar-te que estàs còmode compartint aquest contingut.

## Publicar-ho perquè "tothom" el pugui fer servir (sense saber d'informàtica)

Opció més senzilla i gratuïta: **Streamlit Community Cloud**.

1. Puja el projecte a GitHub (pas anterior)
2. Vés a https://share.streamlit.io i connecta el teu compte de GitHub
3. Selecciona el repositori `pau-bot` i el fitxer `app.py`
4. A "Secrets" (configuració de l'app), afegeix:
   ```
   GEMINI_API_KEY = "la-teva-clau"
   ```
5. Deploy — et donen una URL pública (tipus `pau-bot.streamlit.app`) que
   pots compartir amb qui vulguis, sense que hagin d'instal·lar res.

Alternativa equivalent: **Hugging Face Spaces** (support natiu per a
Streamlit i també per a Docker, si prefereixes desplegar el contenidor
directament).

**Abans de compartir la URL amb "tothom":**
- Revisa el punt de privacitat de dalt (converses de tercers al corpus)
- Ten en compte els límits de la capa gratuïta de Gemini: es comparteixen
  entre TOTS els usuaris de la teva clau — amb molt trànsit, es pot
  esgotar. Per un ús entre amics/coneguts sol anar bé; per difusió massiva,
  considera afegir un límit de missatges per sessió.