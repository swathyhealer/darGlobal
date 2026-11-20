
import json
import logging
from pathlib import Path

import streamlit as st
from websockets.sync.client import connect
from websockets.exceptions import WebSocketException

import config


# ==================================================
# CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="DarGlobal AI Assistant",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMAGE_PATH = (
    Path(__file__).parent
    / "assets"
    / "darglobal_assistant.jpg"
)

WEBSOCKET_URL = config.WEBSOCKET_URL
TOP_K = config.TOP_K


# ==================================================
# SESSION STATE
# ==================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "sources" not in st.session_state:
    st.session_state.sources = []

if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

if "pending_message" not in st.session_state:
    st.session_state.pending_message = None

if "error_message" not in st.session_state:
    st.session_state.error_message = None


# ==================================================
# BLACK & GOLD THEME
# ==================================================

st.markdown(
    """
    <style>

    /* =========================================
       MAIN APPLICATION
    ========================================= */

    .stApp {
        background-color: #080808;
        color: #FFFFFF;
    }

    header[data-testid="stHeader"] {
        background-color: #080808;
    }

    .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }


    /* =========================================
       HEADER
    ========================================= */

    .main-title {
        color: #D4AF37;
        font-size: 38px;
        font-weight: 700;
        text-align: center;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }

    .subtitle {
        color: #C0A45C;
        text-align: center;
        font-size: 15px;
        line-height: 1.6;
        margin-bottom: 20px;
    }

    .gold-divider {
        border: none;
        height: 1px;
        background: linear-gradient(
            to right,
            transparent,
            #D4AF37,
            transparent
        );
        margin: 20px 0;
    }


    /* =========================================
       CHAT MESSAGES
    ========================================= */

    [data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 14px;
        color: #FFFFFF !important;
    }

    /* USER MESSAGE - PURE BLACK */

    [data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-user"]
    ) {
        background-color: #000000 !important;
        border: 1px solid #D4AF37 !important;
        border-left: 4px solid #D4AF37 !important;
    }

    /* ASSISTANT MESSAGE - DARK CHARCOAL */

    [data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-assistant"]
    ) {
        background-color: #171717 !important;
        border: 1px solid #5C4920 !important;
        border-left: 4px solid #B89632 !important;
    }

    /* CHAT TEXT */

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {
        color: #FFFFFF !important;
    }


    /* =========================================
       GOLD CHAT INPUT
    ========================================= */

    [data-testid="stChatInput"] {
        background-color: #D4AF37 !important;
        border: 2px solid #E8C65A !important;
        border-radius: 14px !important;
    }

    /* Input wrapper */

    [data-testid="stChatInput"] > div {
        background-color: #D4AF37 !important;
    }

    /* Typed text */

    [data-testid="stChatInput"] textarea {
        color: #080808 !important;
        background-color: transparent !important;
        caret-color: #080808 !important;
    }

    /* Placeholder */

    [data-testid="stChatInput"] textarea::placeholder {
        color: #493A12 !important;
        opacity: 1 !important;
    }

    /* SEND BUTTON - BLACK */

    [data-testid="stChatInput"] button {
        background-color: #080808 !important;
        border: 1px solid #080808 !important;
        border-radius: 10px !important;
    }

    /* Send icon - GOLD */

    [data-testid="stChatInput"] button svg {
        color: #D4AF37 !important;
        stroke: #D4AF37 !important;
    }

    /* Disabled input while generating */

    [data-testid="stChatInput"]:has(textarea:disabled) {
        opacity: 0.65;
        cursor: not-allowed;
    }

    [data-testid="stChatInput"] button:disabled {
        opacity: 0.45;
        cursor: not-allowed;
    }


    /* =========================================
       LOADING STATUS
    ========================================= */

    [data-testid="stStatusWidget"] {
        background-color: #151515;
        border: 1px solid #8C7026;
        border-radius: 10px;
    }


    /* =========================================
       SIDEBAR
    ========================================= */

    [data-testid="stSidebar"] {
        background-color: #101010;
        border-right: 1px solid #302817;
    }


    /* =========================================
       BUTTONS
    ========================================= */

    .stButton > button {
        background-color: #D4AF37;
        color: #080808;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #F0D477;
        color: #080808;
    }


    /* =========================================
       EXPANDER
    ========================================= */

    [data-testid="stExpander"] {
        background-color: #141414;
        border: 1px solid #5C4920;
        border-radius: 10px;
    }


    /* =========================================
       LINKS
    ========================================= */

    a {
        color: #D4AF37 !important;
    }


    /* =========================================
       SCROLLBAR
    ========================================= */

    ::-webkit-scrollbar {
        width: 6px;
    }

    ::-webkit-scrollbar-thumb {
        background: #8C7026;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# HEADER
# ==================================================

st.markdown(
    """
    <div class="main-title">
        ✨ DARGI - DarGlobal AI Assistant
    </div>


    <hr class="gold-divider">
    """,
    unsafe_allow_html=True,
)


# ==================================================
# ASSISTANT IMAGE
# ==================================================

left, center, right = st.columns([1, 1.4, 1])

with center:

    if IMAGE_PATH.exists():

        st.image(
            str(IMAGE_PATH),
            width=280,
        )
        

    else:

        st.warning(
            "Assistant image not found. "
            "Check the assets directory."
        )
        
# Welcome message below the image
st.markdown(
            """
            <div class="welcome-message">
                <h3>Welcome to DarGlobal !!! </h3>
                <p>
                    DarGlobal is a premier international luxury real estate investment
                    and development platform specialising in architecturally distinctive,
                    design-led residences in the world's most sought-after destinations.
                </p>
                <p>
                    Listed on the London Stock Exchange, we connect global capital with
                    curated luxury living and property investment opportunities across
                    the UAE, Saudi Arabia, Qatar, Spain, and beyond.
                </p>
                <p><strong>How can I assist you today?</strong></p>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown(
    '<hr class="gold-divider">',
    unsafe_allow_html=True,
)


# ==================================================
# WEBSOCKET STREAMING
# ==================================================

def stream_response(message: str, history: list):
    """
    Connect to FastAPI WebSocket and stream
    the LLM response token by token.

    Expected events:

        {"type": "sources", "sources": [...]}
        {"type": "token", "content": "..."}
        {"type": "done"}
        {"type": "error", "message": "..."}
    """

    payload = {
        "message": message,
        "history": history,
        "top_k": TOP_K,
    }

    received_sources = []

    try:

        with connect(
            WEBSOCKET_URL,
            open_timeout=15,
            close_timeout=5,
            max_size=10 * 1024 * 1024,
        ) as websocket:

            # Send user request
            websocket.send(json.dumps(payload))

            while True:

                raw_message = websocket.recv()

                event = json.loads(raw_message)

                event_type = event.get("type")

                # SOURCES
                if event_type == "sources":

                    received_sources.extend(
                        event.get("sources", [])
                    )

                # STREAMING TOKENS
                elif event_type == "token":

                    token = event.get("content", "")

                    if token:
                        yield token

                # COMPLETED
                elif event_type == "done":

                    break

                # ERROR
                elif event_type == "error":

                    raise RuntimeError(
                        event.get(
                            "message",
                            "Unable to generate response."
                        )
                    )

                else:

                    logger.warning(
                        "Unknown WebSocket event: %s",
                        event_type,
                    )

    except WebSocketException as exc:

        logger.exception(
            "WebSocket connection failed"
        )

        raise RuntimeError(
            "Unable to connect to the chatbot server."
        ) from exc

    except json.JSONDecodeError as exc:

        logger.exception(
            "Invalid JSON received from backend"
        )

        raise RuntimeError(
            "Invalid response received from server."
        ) from exc

    finally:

        st.session_state.sources = received_sources


# ==================================================
# DISPLAY CHAT HISTORY
# ==================================================

for chat in st.session_state.chat_history:

    avatar = (
        "👤"
        if chat["role"] == "user"
        else "✨"
    )

    with st.chat_message(
        chat["role"],
        avatar=avatar,
    ):

        st.markdown(chat["content"])

        # Display sources
        if chat["role"] == "assistant" and chat.get("sources"):

            with st.expander("📚 Reference Sources"):

                for index, source in enumerate(
                    chat["sources"],
                    start=1,
                ):

                    title = source.get(
                        "title",
                        f"Source {index}",
                    )

                    url = source.get(
                        "source_url",
                        "",
                    )

                    if url:

                        st.markdown(
                            f"{index}. [{title}]({url})"
                        )

                    else:

                        st.markdown(
                            f"{index}. {title}"
                        )


# ==================================================
# CHAT INPUT
# ==================================================

user_input = st.chat_input(
    "Ask me anything about DarGlobal...",
    disabled=st.session_state.is_generating,
)


# ==================================================
# CAPTURE USER MESSAGE
# ==================================================

if user_input and not st.session_state.is_generating:

    st.session_state.pending_message = user_input
    st.session_state.is_generating = True
    st.session_state.error_message = None

    # Render disabled input before backend processing
    st.rerun()


# ==================================================
# PROCESS PENDING MESSAGE
# ==================================================

if st.session_state.pending_message is not None:

    message = st.session_state.pending_message

    # Previous successful conversation history
    previous_history = [
        {
            "role": item["role"],
            "content": item["content"],
        }
        for item in st.session_state.chat_history
    ]

    # USER MESSAGE
    with st.chat_message("user", avatar="👤"):

        st.markdown(message)

    # ASSISTANT RESPONSE
    with st.chat_message("assistant", avatar="✨"):

        try:

            with st.status(
                "Connecting to DarGlobal AI Assistant...",
                expanded=True,
            ) as status:

                # Stream tokens directly into the chat
                response = st.write_stream(
                    stream_response(
                        message=message,
                        history=previous_history,
                    )
                )

                if not response:

                    response = (
                        "I couldn't generate a response. "
                        "Please try again."
                    )

                status.update(
                    label="Response generated successfully!",
                    state="complete",
                    expanded=False,
                )

            # SAVE USER MESSAGE
            st.session_state.chat_history.append(
                {
                    "role": "user",
                    "content": message,
                }
            )

            # SAVE ASSISTANT RESPONSE
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": response,
                    "sources": st.session_state.sources,
                }
            )

            # DISPLAY SOURCES
            if st.session_state.sources:

                with st.expander("📚 Reference Sources"):

                    for index, source in enumerate(
                        st.session_state.sources,
                        start=1,
                    ):

                        title = source.get(
                            "title",
                            f"Source {index}",
                        )

                        url = source.get(
                            "source_url",
                            "",
                        )

                        if url:

                            st.markdown(
                                f"{index}. [{title}]({url})"
                            )

                        else:

                            st.markdown(
                                f"{index}. {title}"
                            )

        except Exception as exc:

            logger.exception(
                "Chat processing failed"
            )

            st.session_state.error_message = str(exc)

        finally:

            # RESTORE INPUT STATE
            st.session_state.pending_message = None
            st.session_state.is_generating = False

            # Render completed conversation
            st.rerun()


# ==================================================
# DISPLAY ERROR
# ==================================================

if st.session_state.error_message:

    st.error(
        f"Unable to process your request: "
        f"{st.session_state.error_message}"
    )


# ==================================================
# SIDEBAR
# ==================================================

# with st.sidebar:

    st.markdown(
        """
        <h2 style="color:#D4AF37;">
            ✨ DarGlobal
        </h2>

        <p style="color:#C0A45C;">
            Your Intelligent AI Assistant
        </p>

        <hr class="gold-divider">
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"**Total messages:** "
        f"{len(st.session_state.chat_history)}"
    )

    st.markdown("---")

    # if st.button(
    #     "🗑️ Clear Conversation",
    #     use_container_width=True,
    #     disabled=st.session_state.is_generating,
    # ):

    #     st.session_state.chat_history = []
    #     st.session_state.sources = []
    #     st.session_state.error_message = None

    #     st.rerun()

    st.markdown("---")

    st.markdown(
        """
        <p style="
            color:#888888;
            font-size:12px;
            text-align:center;
        ">
            Powered by FastAPI, Qdrant Cloud
            and OpenRouter
        </p>
        """,
        unsafe_allow_html=True,
    )
