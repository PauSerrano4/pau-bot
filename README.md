# Pau-bot — a chatbot that sounds like me

A personal chatbot trained to reply in my own writing style, using real
examples from my WhatsApp and Instagram conversations. Built with
Streamlit and the Gemini API (free tier, no payment required).

**[Try pau-bot online](https://pau-bot.streamlit.app/)**

## Project structure

- `app.py` — Streamlit chat interface.
- `persona_config.py` — builds the system prompt: style description +
  examples (static, or dynamic retrieval if a style index exists).
- `style_retrieval.py` — retrieves the most similar examples to a given
  message in real time.
- `process_all_chats.py` — unzips and parses WhatsApp chat exports from
  a folder.
- `extract_whatsapp_examples.py` — parser for a single WhatsApp chat
  (used by the script above).
- `extract_instagram_examples.py` — parser for Instagram message exports
  (JSON format).
- `debug_chat_format.py` / `debug_discord_export.py` — inspect raw
  export formats for debugging.
- `merge_examples.py` — combines examples from all platforms into one
  corpus.
- `filter_examples.py` — cleans noise (filler replies, very short
  messages) from the merged corpus.
- `build_style_index.py` — generates embeddings for the filtered
  examples.
- `requirements.txt` — dependencies.
- `Dockerfile` / `.dockerignore` — containerization.

## Full pipeline (building your own corpus)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Extract examples from your chats

WhatsApp:
```bash
python3 process_all_chats.py chats/WhatsApp "YourName"
```
Generates `whatsapp_examples.py`.

Instagram (export your data in JSON format, not HTML):
```bash
python3 extract_instagram_examples.py "your_instagram_activity/messages/inbox" "YourName"
```
Generates `instagram_examples.py`.

### 3. Merge everything into one corpus
```bash
python3 merge_examples.py
```
Automatically detects whichever platform files exist and combines them
into `all_extracted_examples.py`.

### 4. Filter out noise
```bash
python3 filter_examples.py
```
Removes filler replies ("ok", "lol", etc.) and very short messages.
Generates `filtered_examples.py`. Worth a quick look in case you want to
exclude an entire conversation for privacy reasons (e.g. family chats).

### 5. Build the style index
```bash
python3 build_style_index.py
```
Generates local embeddings (no API key needed, model downloads
automatically on first run) and saves them to `style_index.pkl`.

With this index, **there's no need to manually curate 15-30 examples**:
the bot dynamically retrieves the 8 most relevant examples for every new
message. If you'd rather keep it simple (fewer, fixed examples), you can
skip steps 3-5 and fill in `FEW_SHOT_EXAMPLES` by hand in
`persona_config.py` — the code automatically falls back to this if
`style_index.pkl` isn't found.

### 6. Set your API key and run
```bash
export GEMINI_API_KEY="your-key"
streamlit run app.py
```
Get a free key at https://aistudio.google.com/apikey — no credit card
required. Uses the `google-genai` SDK with `gemini-3.1-flash-lite` (a
free-tier model with generous daily limits). If this ever errors with
"model not found", Google renames models fairly often — check
https://ai.google.dev/gemini-api/docs/models for the current option.

## Iterating and improving

- If a reply doesn't sound quite right, expand `STYLE_DESCRIPTION` in
  `persona_config.py` with the specific trait that's missing (tone,
  phrasing, message length...).
- To adjust how many examples get retrieved per message, change `k=8` in
  the `get_similar_examples` call inside `persona_config.py`.
- Want the bot to remember actual facts about you (not just style)? The
  natural next step is adding knowledge-based RAG with pgvector.

## Notes

- Default model: `gemini-3.1-flash-lite` (Google AI Studio free tier —
  no payment required, with rate limits that are more than enough for
  personal use). Google renames models fairly often; if you get an
  error, check what's currently available.
- Dynamic retrieval scales much better than static few-shot once you
  have thousands of examples: instead of hand-picking 20 and discarding
  the rest, every message automatically draws on the most relevant
  examples from the whole corpus.

## Containerizing with Docker

```bash
docker build -t pau-bot .
docker run -p 8501:8501 -e GEMINI_API_KEY="your-key" pau-bot
```

Open http://localhost:8501. The image installs the CPU-only build of
PyTorch (much lighter) and pre-downloads the embedding model at build
time, so the container starts up quickly.

## Publishing it for anyone to use (zero technical setup required)

Easiest and free option: **Streamlit Community Cloud**.

1. Push the project to GitHub
2. Go to https://share.streamlit.io and connect your GitHub account
3. Select the `pau-bot` repository and the `app.py` file
4. Under "Secrets" (app settings), add:
   ```
   GEMINI_API_KEY = "your-key"
   ```
5. Deploy — you'll get a public URL (like `pau-bot.streamlit.app`) that
   anyone can use, no installation needed.

Equivalent alternative: **Hugging Face Spaces** (native Streamlit
support, or deploy the Docker container directly).

**Before sharing the URL widely:**
- Make sure no private conversations from third parties ended up in the
  corpus (see `.gitignore` — chat exports and derived files are excluded
  by default).
- Keep in mind the Gemini free tier limits are shared across ALL users
  of your key — with heavy traffic, they can run out. Fine for friends
  and acquaintances; for wider distribution, consider adding a
  per-session message limit.

## Privacy

This project uses real conversations from friends and family to learn a
writing style. The `.gitignore` excludes all exported chats and derived
files (`chats/`, `*_examples.py`, `style_index.pkl`) from version
control by default — they never get pushed to GitHub unless you
explicitly remove them from `.gitignore`. If you fork this project,
review your own corpus before making it public.