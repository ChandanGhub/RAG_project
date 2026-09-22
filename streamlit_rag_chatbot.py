# Owner : CHANDAN
# Contact : Chandansahho@gmail.com


import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from rag_chatbot_backend import (
    chatbot,
    ingest_pdf,
    retrieve_all_threads,
    thread_document_metadata,
)


# =========================== Utilities ===========================
# Changed made
def generate_thread_id():
    """
    Generate a new thread ID.

    IMPORTANT:
    Return a STRING, not a UUID object.
    This keeps thread IDs consistent everywhere.
    """
    return str(uuid.uuid4())


def add_thread(thread_id):
    """
    Add a thread to the list if it doesn't already exist.
    """
    thread_id = str(thread_id)

    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def load_conversation(thread_id):
    """
    Load conversation messages from LangGraph checkpoint.
    """

    thread_id = str(thread_id)

    state = chatbot.get_state(
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return state.values.get("messages", [])


def reset_chat():
    """
    Create a completely new chat.
    """

    new_thread_id = generate_thread_id()

    # Set the new current thread
    st.session_state["thread_id"] = new_thread_id

    # Add it to the known threads
    add_thread(new_thread_id)

    # Clear messages shown in the UI
    st.session_state["message_history"] = []


def switch_thread(thread_id):
    """
    Switch from the current chat to an existing past conversation.
    """

    thread_id = str(thread_id)

    # Change current thread
    st.session_state["thread_id"] = thread_id

    # Load messages from LangGraph
    messages = load_conversation(thread_id)

    # Convert LangChain messages into our UI format
    temp_messages = []

    for msg in messages:

        if isinstance(msg, HumanMessage):
            temp_messages.append(
                {
                    "role": "user",
                    "content": msg.content,
                }
            )

        elif isinstance(msg, AIMessage):
            temp_messages.append(
                {
                    "role": "assistant",
                    "content": msg.content,
                }
            )

        # Ignore ToolMessage in visible chat history
        elif isinstance(msg, ToolMessage):
            continue

    st.session_state["message_history"] = temp_messages


# ============================================================
# Session State Initialization
# ============================================================

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []


if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()


if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = list(
        retrieve_all_threads()
    )


if "ingested_docs" not in st.session_state:
    st.session_state["ingested_docs"] = {}


# Make sure current thread exists
add_thread(
    st.session_state["thread_id"]
)


# ============================================================
# Current Thread
# ============================================================

thread_key = st.session_state["thread_id"]


# Make sure this thread has a document dictionary
thread_docs = st.session_state["ingested_docs"].setdefault(
    thread_key,
    {}
)


# Past conversations
threads = list(
    st.session_state["chat_threads"]
)[::-1]


# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("LangGraph Chatbot: PDF")


# ------------------------------------------------------------
# Current Thread ID
# ------------------------------------------------------------

st.sidebar.markdown(
    f"**Thread ID:** `{thread_key}`"
)


# ------------------------------------------------------------
# New Chat
# ------------------------------------------------------------

if st.sidebar.button(
    "🆕 New Chat",
    use_container_width=True,
):

    reset_chat()

    st.rerun()


# ------------------------------------------------------------
# Current PDF
# ------------------------------------------------------------

# First check backend metadata
doc_meta = thread_document_metadata(thread_key)


if doc_meta:

    st.sidebar.success(
        f"Using `{doc_meta.get('filename', 'PDF')}` "
        f"({doc_meta.get('chunks', '?')} chunks, "
        f"{doc_meta.get('documents', '?')} pages)"
    )

# Otherwise check current session
elif thread_docs:

    latest_doc = list(thread_docs.values())[-1]

    st.sidebar.success(
        f"Using `{latest_doc.get('filename', 'PDF')}` "
        f"({latest_doc.get('chunks', '?')} chunks from "
        f"{latest_doc.get('documents', '?')} pages)"
    )

else:

    st.sidebar.info(
        "No PDF doc. indexed yet."
    )


# ============================================================
# PDF Upload
# ============================================================

uploaded_pdf = st.sidebar.file_uploader(
    "Upload a PDF for this chat",
    type=["pdf"],
)


if uploaded_pdf:

    # Check if this PDF was already processed
    already_processed = (
        uploaded_pdf.name in thread_docs
    )

    if already_processed:

        st.sidebar.info(
            f"`{uploaded_pdf.name}` already processed for this chat."
        )

    else:

        with st.sidebar.status(
            "Indexing PDF...",
            expanded=True,
        ) as status_box:

            summary = ingest_pdf(
                uploaded_pdf.getvalue(),
                thread_id=thread_key,
                filename=uploaded_pdf.name,
            )

            # Store information for this thread
            thread_docs[uploaded_pdf.name] = summary

            status_box.update(
                label="✅ PDF indexed successfully",
                state="complete",
                expanded=False,
            )


# ============================================================
# Past Conversations
# ============================================================

st.sidebar.subheader(
    "Past conversations"
)


if not threads:

    st.sidebar.write(
        "No past conversations yet."
    )

else:

    for past_thread_id in threads:

        past_thread_id = str(past_thread_id)

        # Try to get document name for nicer display
        past_doc = thread_document_metadata(
            past_thread_id
        )

        if past_doc:

            button_label = (
                f"📄 {past_doc.get('filename', 'PDF Chat')}"
            )

        else:

            # Keep UUID as fallback
            button_label = (
                f"💬 {past_thread_id[:8]}..."
            )

        st.sidebar.button(
            button_label,
            key=f"side-thread-{past_thread_id}",
            use_container_width=True,
            on_click=switch_thread,
            args=(past_thread_id,),
        )


# ============================================================
# Main Layout
# ============================================================

st.title("RAG Chatbot (PDF)")


# ============================================================
# Current Thread Information
# ============================================================

st.caption(
    f"Current Thread: `{thread_key}`"
)


# ============================================================
# Chat History
# ============================================================

for message in st.session_state["message_history"]:

    with st.chat_message(
        message["role"]
    ):

        st.write(
            message["content"]
        )


# ============================================================
# Chat Input
# ============================================================

user_input = st.chat_input(
    "Ask about your document or use tools..."
)


if user_input:

    # --------------------------------------------------------
    # Save user message in frontend history
    # --------------------------------------------------------

    st.session_state["message_history"].append(
        {
            "role": "user",
            "content": user_input,
        }
    )


    # --------------------------------------------------------
    # Display user message
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.write(user_input)


    # --------------------------------------------------------
    # LangGraph configuration
    # --------------------------------------------------------

    CONFIG = {

        "configurable": {
            "thread_id": thread_key,
        },

        "metadata": {
            "thread_id": thread_key,
        },

        "run_name": "chat_turn",
    }


    # --------------------------------------------------------
    # Assistant response
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        status_holder = {
            "box": None
        }


        def ai_only_stream():

            for message_chunk, metadata in chatbot.stream(

                {
                    "messages": [
                        HumanMessage(
                            content=user_input
                        )
                    ]
                },

                config=CONFIG,

                stream_mode="messages",
            ):

                # --------------------------------------------
                # Tool message
                # --------------------------------------------

                if isinstance(
                    message_chunk,
                    ToolMessage,
                ):

                    tool_name = getattr(
                        message_chunk,
                        "name",
                        "tool",
                    )


                    if status_holder["box"] is None:

                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}`...",
                            expanded=True,
                        )

                    else:

                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}`...",
                            state="running",
                            expanded=True,
                        )


                # --------------------------------------------
                # AI message
                # --------------------------------------------

                if isinstance(
                    message_chunk,
                    AIMessage,
                ):

                    # content can sometimes be empty
                    if message_chunk.content:

                        yield message_chunk.content


        # Stream assistant response
        ai_message = st.write_stream(
            ai_only_stream()
        )


        # ----------------------------------------------------
        # Finish tool status
        # ----------------------------------------------------

        if status_holder["box"] is not None:

            status_holder["box"].update(
                label="✅ Tool finished",
                state="complete",
                expanded=False,
            )


    # --------------------------------------------------------
    # Save assistant response
    # --------------------------------------------------------

    st.session_state["message_history"].append(
        {
            "role": "assistant",
            "content": ai_message,
        }
    )


    # --------------------------------------------------------
    # Display document information
    # --------------------------------------------------------

    doc_meta = thread_document_metadata(
        thread_key
    )


    if doc_meta:

        st.caption(
            f"Document indexed: "
            f"{doc_meta.get('filename', 'Unknown')} "
            f"(chunks: "
            f"{doc_meta.get('chunks', '?')}, "
            f"pages: "
            f"{doc_meta.get('documents', '?')})"
        )


# ============================================================
# Bottom Divider
# ============================================================

st.divider()
