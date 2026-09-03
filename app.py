"""
Personal-style chatbot.

Uses the Gemini API (Google AI Studio free tier) via the `google-genai`
SDK — no payment required, only rate limits apply.

Local run:
    pip install streamlit google-genai
    export GEMINI_API_KEY="your-key"
    streamlit run app.py

Get a free API key at https://aistudio.google.com/apikey
"""

import os
import time
import warnings

import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

from persona_config import build_system_prompt

# Silence harmless torchvision warnings (transformers tries to load
# optional image/video components we don't need, since we only process
# text)
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
# NOTE (September 2026): Google significantly cut free-tier limits for
# "regular" Gemini 3.x models (gemini-3.7-flash: only 20 requests/day!).
# "Flash-lite" models have much more generous daily limits (900-1500/day)
# and work great for style-mimicking, which doesn't need deep reasoning.
# MODEL_FALLBACK kicks in if the primary model fails (server overload or
# quota exhausted). If this ever errors with "model not found" or limits
# change again, check https://ai.google.dev/gemini-api/docs/rate-limits
MODEL = "gemini-3.1-flash-lite"
MODEL_FALLBACK = "gemini-2.5-flash-lite"
MAX_TOKENS = 1024
MAX_RETRIES = 3
MAX_MESSAGES_PER_SESSION = 20  # keeps one visitor from draining the shared free quota

st.set_page_config(page_title="Pau-bot", page_icon="🗣️")
st.title("🗣️ Pau-bot")
st.markdown(
    "Chat with a bot trained to sound just like Pau. Type a message below "
    "to get started!"
)
st.info(
    "The first reply may take a little longer than usual while things "
    "warm up — after that, responses come back quickly.",
    icon="💡",
)

api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error(
        "Missing GEMINI_API_KEY environment variable. "
        "Run `export GEMINI_API_KEY=your-key` before starting the app. "
        "Get a free key at https://aistudio.google.com/apikey"
    )
    st.stop()

client = genai.Client(api_key=api_key)

# --------------------------------------------------------------------------
# Chat state
# --------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "message_count" not in st.session_state:
    st.session_state.message_count = 0

for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🗣️"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --------------------------------------------------------------------------
# User input
# --------------------------------------------------------------------------
user_input = st.chat_input("Type a message, as if you were texting Pau...")

def call_gemini_with_retry(contents, system_prompt):
    """Calls the API with retries and fallback if the primary model is
    overloaded (503) or has run out of daily/per-minute quota (429)."""
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
                    time.sleep(2 ** attempt)  # wait 1s, 2s, 4s
                    continue
                raise  # other server errors, don't retry
            except ClientError as e:
                last_error = e
                if getattr(e, "code", None) == 429:
                    # Quota exhausted (daily or per-minute): retrying the
                    # same model won't help if it's the daily limit, so
                    # move straight to the next model.
                    break
                raise  # other client errors (malformed request, etc.)
        # retries exhausted (or quota hit) with this model

    raise last_error


if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    if st.session_state.message_count >= MAX_MESSAGES_PER_SESSION:
        # Session limit reached: don't call the API at all, just explain
        # clearly instead of the user hitting a confusing quota error.
        reply = (
            f"🚦 You've reached this session's limit of "
            f"{MAX_MESSAGES_PER_SESSION} messages. This keeps the free "
            f"quota available for everyone — refresh the page to start a "
            f"new session, or come back in a bit!"
        )
        with st.chat_message("assistant", avatar="🗣️"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
    else:
        st.session_state.message_count += 1

        with st.chat_message("assistant", avatar="🗣️"):
            with st.spinner("Thinking of how Pau would put it..."):
                system_prompt = build_system_prompt(user_message=user_input)

                # The new SDK uses "user"/"model" instead of "user"/"assistant"
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
                        "⚠️ This chatbot has hit its free usage limit for now. "
                        "Please try again in a little while!"
                    )
                except ServerError:
                    reply = (
                        "⚠️ The AI service is a bit overloaded right now. "
                        "Please try again shortly."
                    )
                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

# --------------------------------------------------------------------------
# Sidebar with helpful info
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("About this bot")
    st.write(
        "I trained this chatbot on my own writing style, using real "
        "conversations, so it replies the way I actually would — same "
        "tone, same phrasing, same vibe."
    )
    st.write(
        "**Cost:** completely free to use. It runs on a free-tier AI "
        "service, so replies might occasionally be a bit slower during "
        "busy periods."
    )
    st.write(
        "**Heads up:** this is just a fun personal project, not really "
        "me — treat what it says accordingly!"
    )
    st.caption(
        f"Messages used this session: "
        f"{st.session_state.message_count}/{MAX_MESSAGES_PER_SESSION}"
    )
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption(
        "Built by Pau · "
        "[GitHub](https://github.com/PauSerrano4/pau-bot) · "
        "[LinkedIn](https://www.linkedin.com/in/pauserranosanz/)"
    )