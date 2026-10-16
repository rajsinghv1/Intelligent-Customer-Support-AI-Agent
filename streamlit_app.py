
import hashlib
import re
from pathlib import Path

import streamlit as st

from app.core.config import (
    APP_NAME,
    GEMINI_MODEL,
    BASE_DIR,
)
from app.database.db import (
    init_database,
    create_conversation,
    get_conversations,
    get_messages,
    delete_conversation,
)
from app.services.chat_service import (
    process_customer_message,
    retry_last_message,
)
from app.rag.document_loader import load_document
from app.rag.text_splitter import split_documents
from app.rag.vector_store import (
    add_documents,
    vector_store_exists,
)


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
)


@st.cache_resource
def initialize_app():
    init_database()
    return True


initialize_app()


UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def start_new_chat():
    st.session_state.conversation_id = (
        create_conversation()
    )


if "conversation_id" not in st.session_state:
    conversations = get_conversations()

    if conversations:
        st.session_state.conversation_id = (
            conversations[0]["id"]
        )
    else:
        start_new_chat()


if "use_rag" not in st.session_state:
    st.session_state.use_rag = True


# ----------------------------------
# SIDEBAR
# ----------------------------------

with st.sidebar:
    st.title("🤖 Support AI")
    st.caption("Customer Support Platform")

    page = st.radio(
        "Navigation",
        ["AI Chat", "Knowledge Base"],
    )

    st.divider()

    if page == "AI Chat":
        if st.button(
            "➕ New Conversation",
            use_container_width=True,
        ):
            start_new_chat()
            st.rerun()

        st.subheader("Chat History")

        for conversation in get_conversations():
            conversation_id = conversation["id"]

            if st.button(
                conversation["title"],
                key=f"chat_{conversation_id}",
                use_container_width=True,
            ):
                st.session_state.conversation_id = (
                    conversation_id
                )
                st.rerun()

        if st.button(
            "🗑️ Delete Current Chat",
            use_container_width=True,
        ):
            delete_conversation(
                st.session_state.conversation_id
            )

            remaining = get_conversations()

            if remaining:
                st.session_state.conversation_id = (
                    remaining[0]["id"]
                )
            else:
                start_new_chat()

            st.rerun()

        st.divider()

        st.toggle(
            "Use RAG Knowledge Base",
            key="use_rag",
        )

        if vector_store_exists():
            st.success("Knowledge base available")
        else:
            st.info("No knowledge base indexed")

    st.divider()
    st.caption(f"Model: {GEMINI_MODEL}")
    st.caption("Database: SQLite")
    st.caption("Phase 2: RAG Integration")


# ----------------------------------
# KNOWLEDGE BASE PAGE
# ----------------------------------

if page == "Knowledge Base":
    st.title("📚 Knowledge Base")
    st.write(
        "Upload PDF or TXT documents to provide "
        "company-specific customer support knowledge."
    )

    uploaded_files = st.file_uploader(
        "Upload company documents",
        type=["pdf", "txt"],
        accept_multiple_files=True,
    )

    if st.button(
        "Process Documents",
        type="primary",
    ):
        if not uploaded_files:
            st.warning(
                "Please upload at least one document."
            )
        else:
            for uploaded_file in uploaded_files:
                try:
                    data = uploaded_file.getvalue()

                    if len(data) > 10 * 1024 * 1024:
                        raise ValueError(
                            "Maximum file size is 10 MB."
                        )

                    if not data:
                        raise ValueError(
                            "Uploaded file is empty."
                        )

                    original_name = Path(
                        uploaded_file.name
                    ).name

                    safe_name = re.sub(
                        r"[^a-zA-Z0-9._-]",
                        "_",
                        original_name,
                    )

                    if not safe_name.lower().endswith(
                        (".pdf", ".txt")
                    ):
                        raise ValueError(
                            "Unsupported file type."
                        )

                    digest = hashlib.sha256(
                        data
                    ).hexdigest()[:12]

                    saved_name = (
                        f"{digest}_{safe_name}"
                    )

                    saved_path = (
                        UPLOAD_DIR / saved_name
                    )

                    if saved_path.exists():
                        st.info(
                            f"{original_name}: already "
                            "uploaded. Skipping duplicate."
                        )
                        continue

                    saved_path.write_bytes(data)

                    try:
                        documents = load_document(
                            saved_path
                        )

                        chunks = split_documents(
                            documents
                        )

                        count = add_documents(
                            chunks
                        )

                    except Exception:
                        saved_path.unlink(
                            missing_ok=True
                        )
                        raise

                    st.success(
                        f"{original_name}: "
                        f"{count} chunks indexed."
                    )

                except Exception as error:
                    st.error(
                        f"Failed to process "
                        f"{uploaded_file.name}"
                    )
                    st.exception(error)

    st.divider()

    st.subheader("Knowledge Base Status")

    if vector_store_exists():
        st.success(
            "FAISS vector database is ready."
        )
    else:
        st.warning(
            "Upload and process documents "
            "to initialize the vector database."
        )

    st.caption(
        "Use only trusted, non-sensitive documents. "
        "This local prototype does not yet have "
        "user authentication or access controls."
    )


# ----------------------------------
# AI CHAT PAGE
# ----------------------------------

else:
    st.title("🤖 Intelligent Customer Support")

    st.caption(
        "AI-powered support with Google Gemini + RAG"
    )

    if st.session_state.use_rag:
        if vector_store_exists():
            st.success(
                "RAG mode enabled: company knowledge base"
            )
        else:
            st.info(
                "RAG selected, but no knowledge base "
                "is indexed. General Gemini chat is active."
            )
    else:
        st.info(
            "General Gemini chat mode is active."
        )

    current_id = st.session_state.conversation_id

    messages = get_messages(current_id)

    if not messages:
        st.markdown("### 👋 Welcome!")
        st.write(
            "Ask a customer support question "
            "to get started."
        )

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    pending_reply = (
        bool(messages)
        and messages[-1]["role"] == "user"
    )

    if pending_reply:
        st.warning(
            "The last message is awaiting "
            "an AI response."
        )

        if st.button("🔄 Retry AI Response"):
            with st.spinner(
                "Generating response..."
            ):
                try:
                    retry_last_message(
                        current_id,
                        use_rag=st.session_state.use_rag,
                    )
                except Exception as error:
                    st.error("AI response failed.")
                    st.exception(error)
                else:
                    st.rerun()

    user_prompt = st.chat_input(
        "Ask your customer support question...",
        disabled=pending_reply,
    )

    if user_prompt:
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("AI is thinking..."):
                try:
                    response = process_customer_message(
                        current_id,
                        user_prompt,
                        use_rag=st.session_state.use_rag,
                    )

                    st.markdown(response)

                except Exception as error:
                    st.error(
                        "Unable to generate a response."
                    )
                    st.exception(error)

                else:
                    st.rerun()
