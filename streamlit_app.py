import streamlit as st

from config import SYSTEM_PROMPT
from llm import stream_chat

from conversations import (
    load_active_history,
    save_active_history,
    save_conversation,
    load_conversation,
    list_conversations,
    rename_conversation,
    new_history,
)


st.set_page_config(
    page_title="LocalChat",
    page_icon="🤖",
    layout="wide"
)


# -------------------------
# INITIALISATION
# -------------------------

if "history" not in st.session_state:
    st.session_state.history = load_active_history(
        SYSTEM_PROMPT
    )


# -------------------------
# SIDEBAR
# -------------------------

with st.sidebar:
    st.title("🤖 LocalChat")

    if st.button(
        "➕ Nouveau chat",
        use_container_width=True
    ):
        st.session_state.history = new_history(
            SYSTEM_PROMPT
        )

        save_active_history(
            st.session_state.history
        )

        st.rerun()

    st.divider()

    st.subheader("Conversations")

    conversations = list_conversations()

    if conversations:

        selected_conversation = st.selectbox(
            "Conversation",
            conversations
        )

        if st.button(
            "📂 Charger",
            use_container_width=True
        ):
            history, error = load_conversation(
                selected_conversation,
                SYSTEM_PROMPT
            )

            if history is not None:
                st.session_state.history = history

                save_active_history(history)

                st.rerun()

            else:
                st.error(error)

    else:
        st.caption(
            "Aucune conversation sauvegardée."
        )

    st.divider()

    st.subheader("Sauvegarder")

    save_name = st.text_input(
        "Nom de la conversation",
        placeholder="Ex : Révisions Prolog"
    )

    if st.button(
        "💾 Sauvegarder",
        use_container_width=True
    ):
        success, error = save_conversation(
            st.session_state.history,
            save_name
        )

        if success:
            st.success(
                f'"{save_name}" sauvegardée.'
            )

        else:
            st.error(error)

    st.divider()

    if conversations:
        st.subheader("Renommer")

        rename_source = st.selectbox(
            "Conversation à renommer",
            conversations,
            key="rename_source"
        )

        rename_target = st.text_input(
            "Nouveau nom"
        )

        if st.button(
            "✏️ Renommer",
            use_container_width=True
        ):
            success, error = rename_conversation(
                rename_source,
                rename_target
            )

            if success:
                st.success(
                    "Conversation renommée."
                )

                st.rerun()

            else:
                st.error(error)


# -------------------------
# CHAT
# -------------------------

st.title("LocalChat")

st.caption(
    "Mistral exécuté localement avec Ollama"
)


for message in st.session_state.history:

    if message["role"] == "system":
        continue

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -------------------------
# NOUVEAU MESSAGE
# -------------------------

prompt = st.chat_input(
    "Écris un message..."
)


if prompt:

    with st.chat_message("user"):
        st.markdown(prompt)

    request_history = (
        st.session_state.history
        + [
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    with st.chat_message("assistant"):

        placeholder = st.empty()

        full_response = ""

        try:

            for chunk in stream_chat(
                request_history
            ):
                full_response += chunk

                placeholder.markdown(
                    full_response + "▌"
                )

            placeholder.markdown(
                full_response
            )

        except Exception:
            st.error(
                "Impossible de contacter Ollama. "
                "Vérifie que `ollama serve` est lancé."
            )

    if full_response:

        st.session_state.history.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        st.session_state.history.append(
            {
                "role": "assistant",
                "content": full_response
            }
        )

        save_active_history(
            st.session_state.history
        )