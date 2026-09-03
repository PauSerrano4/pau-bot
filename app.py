"""
Chatbot que imita el teu estil comunicatiu.

Fa servir la Gemini API (capa gratuïta de Google AI Studio) amb el nou
SDK unificat `google-genai` — no cal targeta de pagament, només límits
de peticions per minut/dia.

Execució local:
    pip install streamlit google-genai
    export GEMINI_API_KEY="la-teva-clau"
    streamlit run app.py

La clau API la treus (gratis) a https://aistudio.google.com/apikey
"""

import os
import time
import warnings

import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

from persona_config import build_system_prompt

# Silencia els avisos inofensius de torchvision (transformers intenta
# carregar components d'imatge/vídeo que no fem servir, ja que només
# processem text)
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

# --------------------------------------------------------------------------
# Configuració
# --------------------------------------------------------------------------
# IMPORTANT (setembre 2026): Google ha retallat molt els límits gratuïts
# dels models Gemini 3.x "normals" (gemini-3.7-flash: només 20
# peticions/dia!). Els models "flash-lite" tenen límits diaris molt més
# generosos (900-1500/dia) i van perfectes per imitar estil, que no
# necessita raonament complex. MODEL_FALLBACK s'usa si el principal
# falla (servidor saturat o quota exhaurida). Si en el futur dona error
# "model not found" o els límits tornen a canviar, consulta
# https://ai.google.dev/gemini-api/docs/rate-limits
MODEL = "gemini-3.1-flash-lite"
MODEL_FALLBACK = "gemini-2.5-flash-lite"
MAX_TOKENS = 1024
MAX_RETRIES = 3

st.set_page_config(page_title="Pau-bot", page_icon="🗣️")
st.title("🗣️ Pau-bot")
st.caption("Chatbot entrenat per sonar com tu (few-shot, sense fine-tuning, 100% gratis)")

api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error(
        "Falta la variable d'entorn GEMINI_API_KEY. "
        "Fes `export GEMINI_API_KEY=la-teva-clau` abans d'executar. "
        "La pots crear gratis a https://aistudio.google.com/apikey"
    )
    st.stop()

client = genai.Client(api_key=api_key)

# --------------------------------------------------------------------------
# Estat del xat
# --------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------------------------------------------------------
# Input de l'usuari
# --------------------------------------------------------------------------
user_input = st.chat_input("Escriu un missatge com si li escrivissis a Pau...")

def call_gemini_with_retry(contents, system_prompt):
    """Crida a l'API amb reintents i fallback si el model principal
    està saturat (503) o ha exhaurit la quota diària/per minut (429)."""
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=MAX_TOKENS,
        thinking_config=types.ThinkingConfig(thinking_level="low"),
    )

    last_error = None
    for model in (MODEL, MODEL_FALLBACK):
        for attempt in range(MAX_RETRIES):
            try:
                return client.models.generate_content(
                    model=model, contents=contents, config=config
                )
            except ServerError as e:
                last_error = e
                if getattr(e, "code", None) == 503:
                    time.sleep(2 ** attempt)  # espera 1s, 2s, 4s
                    continue
                raise  # altres errors de servidor, no reintentem
            except ClientError as e:
                last_error = e
                if getattr(e, "code", None) == 429:
                    # Quota exhaurida (diària o per minut): reintentar amb
                    # el mateix model no serveix de res si és el límit
                    # diari, així que passem directament al següent model.
                    break
                raise  # altres errors de client (petició mal formada, etc.)
        # esgotats els reintents (o quota exhaurida) amb aquest model

    raise last_error


if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Pensant com ho diria Pau..."):
            system_prompt = build_system_prompt(user_message=user_input)

            # El nou SDK fa servir "user"/"model" en lloc de "user"/"assistant"
            contents = [
                types.Content(
                    role="user" if m["role"] == "user" else "model",
                    parts=[types.Part(text=m["content"])],
                )
                for m in st.session_state.messages
            ]

            try:
                response = call_gemini_with_retry(contents, system_prompt)
                reply = response.text
            except ClientError:
                reply = (
                    "⚠️ S'ha exhaurit la quota gratuïta de Gemini per avui "
                    "(o per aquest minut). Torna-ho a provar més tard, o "
                    "revisa el teu ús a https://ai.dev/rate-limit"
                )
            except ServerError:
                reply = (
                    "⚠️ Els servidors de Gemini estan saturats ara mateix. "
                    "Torna-ho a provar d'aquí una estona."
                )
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --------------------------------------------------------------------------
# Sidebar amb info útil
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("Sobre aquest bot")
    st.write(
        "Aquest bot fa servir *few-shot prompting*: al `persona_config.py` "
        "hi ha exemples reals del teu estil que es passen com a context "
        "al model abans de cada resposta."
    )
    st.write(
        f"**Cost:** fa servir la capa gratuïta de la Gemini API "
        f"({MODEL}). Sense targeta de pagament, amb límits de peticions "
        f"per minut/dia que per a ús personal van sobrats."
    )
    st.write(
        "**Per millorar-lo:** afegeix més exemples variats a "
        "`FEW_SHOT_EXAMPLES` dins `persona_config.py`, o genera l'índex "
        "d'estil amb `build_style_index.py` per a retrieval dinàmic."
    )
    if st.button("Neteja la conversa"):
        st.session_state.messages = []
        st.rerun()