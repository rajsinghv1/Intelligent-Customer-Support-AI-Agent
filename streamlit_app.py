
import hashlib
import re
from pathlib import Path

import streamlit as st

from app.core.config import APP_NAME, GEMINI_MODEL, BASE_DIR

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

from app.services.classification_service import (
    analyze_customer_message,
)

from app.services.ticket_service import (
    process_customer_ticket,
)

from app.database.ticket_db import (
    init_ticket_db,
    get_ticket,
    list_tickets,
    message_fingerprint,
)

from app.dashboard.ticket_dashboard import (
    render_ticket_dashboard,
)


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
)


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

@st.cache_resource
def initialize_app():
    init_database()
    init_ticket_db()
    return True


initialize_app()

UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# SESSION STATE
# ==========================================

def start_new_chat():
    st.session_state.conversation_id = create_conversation()


if "conversation_id" not in st.session_state:
    conversations = get_conversations()

    if conversations:
        st.session_state.conversation_id = conversations[0]["id"]
    else:
        start_new_chat()


if "use_rag" not in st.session_state:
    st.session_state.use_rag = True


if "ticket_results" not in st.session_state:
    st.session_state.ticket_results = {}


# ==========================================
# CUSTOMER CLASSIFICATION & TICKETING
# ==========================================

def get_ticket_customer_id(conversation_id):
    return f"conversation-{conversation_id}"


def analyze_and_create_ticket(
    conversation_id,
    customer_message,
):
    classification = analyze_customer_message(
        customer_message
    )

    result = process_customer_ticket(
        customer_id=get_ticket_customer_id(
            conversation_id
        ),
        customer_message=customer_message,
        classification=classification,
    )

    return result


def render_ticket_result(result):
    classification = result.get("classification", {})

    st.markdown("#### 🧠 AI Customer Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        intent = str(
            classification.get("intent", "unknown")
        )
        st.write(
            "**Intent:**",
            intent.replace("_", " ").title(),
        )

    with col2:
        sentiment = str(
            classification.get("sentiment", "unknown")
        )
        st.write(
            "**Sentiment:**",
            sentiment.title(),
        )

    with col3:
        urgency = str(
            classification.get("urgency", "unknown")
        )
        st.write(
            "**Urgency:**",
            urgency.title(),
        )

    ticket_id = result.get("ticket_id")

    if ticket_id:
        ticket = get_ticket(ticket_id)

        if result.get("ticket_created"):
            st.success(
                f"🎫 Support Ticket Created: {ticket_id}"
            )
        else:
            st.info(
                f"🎫 Existing Support Ticket: {ticket_id}"
            )

        if ticket:
            status = str(ticket.get("status", "open"))
            st.caption(
                "Ticket Status: "
                + status.replace("_", " ").title()
            )
    else:
        st.info("No support ticket required.")


# ==========================================
# SAVED TICKET ANALYSIS
# ==========================================

def get_saved_ticket_result(
    conversation_id,
    customer_message,
):
    customer_id = get_ticket_customer_id(
        conversation_id
    )

    fingerprint = message_fingerprint(
        customer_message
    )

    # Use the existing public ticket API.
    # Avoid depending on an internal DB connection.
    tickets = list_tickets(limit=500)

    for ticket in tickets:
        if (
            str(ticket.get("customer_id")) == customer_id
            and ticket.get("message_hash") == fingerprint
        ):
            return {
                "ticket_created": False,
                "ticket_id": ticket["ticket_id"],
                "reason": "existing",
                "classification": {
                    "intent": ticket.get(
                        "intent", "unknown"
                    ),
                    "sentiment": ticket.get(
                        "sentiment", "neutral"
                    ),
                    "urgency": ticket.get(
                        "urgency", "low"
                    ),
                    "requires_ticket": True,
                    "summary": ticket.get(
                        "summary", ""
                    ),
                },
            }

    return None


def render_saved_analysis(
    conversation_id,
    message_index,
    customer_message,
):
    key = (conversation_id, message_index)

    result = st.session_state.ticket_results.get(
        key
    )

    if result is None:
        try:
            result = get_saved_ticket_result(
                conversation_id,
                customer_message,
            )
        except Exception:
            result = None

    if result:
        render_ticket_result(result)


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.title("🤖 Support AI")
    st.caption("Intelligent Customer Support Platform")

    page = st.radio(
        "Navigation",
        [
            "AI Chat",
            "Knowledge Base",
            "Support Tickets",
        ],
    )

    st.divider()

    if page == "AI Chat":

        if st.button(
            "➕ New Conversation",
            width="stretch",
        ):
            start_new_chat()
            st.rerun()

        st.subheader("Chat History")

        conversations = get_conversations()

        for conversation in conversations:
            conversation_id = conversation["id"]

            if st.button(
                conversation["title"],
                key=f"chat_{conversation_id}",
                width="stretch",
            ):
                st.session_state.conversation_id = (
                    conversation_id
                )
                st.rerun()

        if st.button(
            "🗑️ Delete Current Chat",
            width="stretch",
        ):
            old_id = st.session_state.conversation_id

            delete_conversation(old_id)

            st.session_state.ticket_results = {
                key: value
                for key, value
                in st.session_state.ticket_results.items()
                if key[0] != old_id
            }

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
    st.caption("AI Support + RAG + Ticketing")


# ==========================================
# KNOWLEDGE BASE PAGE
# ==========================================

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
        "Upload trusted, non-sensitive documents. "
        "This prototype does not yet include "
        "user authentication or access controls."
    )


# ==========================================
# SUPPORT TICKETS PAGE
# ==========================================

elif page == "Support Tickets":

    render_ticket_dashboard()


# ==========================================
# AI CHAT PAGE
# ==========================================

elif page == "AI Chat":

    st.title("🤖 Intelligent Customer Support")

    st.caption(
        "AI-powered support using Google Gemini, "
        "RAG, Customer Classification and Ticketing"
    )

    if st.session_state.use_rag:

        if vector_store_exists():
            st.success(
                "RAG mode enabled: "
                "company knowledge base available."
            )

        else:
            st.info(
                "RAG selected, but no knowledge base "
                "is indexed. General Gemini chat "
                "is active."
            )

    else:
        st.info(
            "General Gemini chat mode is active."
        )

    current_id = (
        st.session_state.conversation_id
    )

    messages = get_messages(current_id)

    if not messages:
        st.markdown("### 👋 Welcome!")

        st.write(
            "Ask a customer support question "
            "to get started."
        )

    # --------------------------------------
    # DISPLAY CHAT HISTORY
    # --------------------------------------

    last_user_index = None

    for index, message in enumerate(messages):

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if message["role"] == "user":
                last_user_index = index

            elif (
                message["role"] == "assistant"
                and last_user_index is not None
            ):
                render_saved_analysis(
                    current_id,
                    last_user_index,
                    messages[last_user_index]["content"],
                )

    # --------------------------------------
    # RETRY FAILED AI RESPONSE
    # --------------------------------------

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
                    st.error(
                        "AI response failed."
                    )
                    st.exception(error)

                else:
                    st.rerun()

    # --------------------------------------
    # NEW CUSTOMER MESSAGE
    # --------------------------------------

    user_prompt = st.chat_input(
        "Ask your customer support question...",
        disabled=pending_reply,
    )

    if user_prompt:

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):

            with st.spinner(
                "AI is thinking..."
            ):

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
                    # ------------------------------
                    # CUSTOMER CLASSIFICATION
                    # ------------------------------

                    try:
                        ticket_result = (
                            analyze_and_create_ticket(
                                current_id,
                                user_prompt,
                            )
                        )

                        updated_messages = (
                            get_messages(current_id)
                        )

                        last_user_index = next(
                            (
                                index
                                for index in range(
                                    len(updated_messages) - 1,
                                    -1,
                                    -1,
                                )
                                if updated_messages[index]["role"]
                                == "user"
                            ),
                            None,
                        )

                        if last_user_index is not None:

                            key = (
                                current_id,
                                last_user_index,
                            )

                            st.session_state.ticket_results[
                                key
                            ] = ticket_result

                        render_ticket_result(
                            ticket_result
                        )

                    except Exception as error:
                        st.warning(
                            "AI response generated, "
                            "but ticket analysis is "
                            "temporarily unavailable."
                        )
                        st.exception(error)

                    st.rerun()
