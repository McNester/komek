import streamlit as st
from dataclasses import dataclass
from pipeline import rag_pipeline
import uuid
from common.models import Message
from chroma.chroma import store_chat_message, load_chat_history, store_chat_session, get_all_chat_sessions

USER = "user"
ASSISTANT = "ai"
MESSAGES = "messages"
CURRENT_CHAT_KEY = "chat_id"
CHAT_SELECTION_KEY = "selected_chat"

def init_session_state():
    # Initialize all required session state variables
    if CURRENT_CHAT_KEY not in st.session_state:
        st.session_state[CURRENT_CHAT_KEY] = None
    if MESSAGES not in st.session_state:
        st.session_state[MESSAGES] = []
    if CHAT_SELECTION_KEY not in st.session_state:
        st.session_state[CHAT_SELECTION_KEY] = "New chat..."
    if "initialized" not in st.session_state:
        st.session_state.initialized = False

def on_chat_selected():
    """Callback for when a chat is selected from the dropdown"""
    selected = st.session_state[CHAT_SELECTION_KEY]
    
    # If selection is the same as current, do nothing
    if selected == st.session_state[CURRENT_CHAT_KEY]:
        return
        
    if selected == "New chat...":
        # Create a new chat
        new_id = str(uuid.uuid4())
        st.session_state[CURRENT_CHAT_KEY] = new_id
        st.session_state[MESSAGES] = [Message(actor=ASSISTANT, payload="Hi! How can I help you?")]
        store_chat_session(new_id)
    else:
        # Load existing chat
        st.session_state[CURRENT_CHAT_KEY] = selected
        loaded_messages = load_chat_history(selected)
        if loaded_messages:
            st.session_state[MESSAGES] = loaded_messages
        else:
            # Fallback if loading fails
            st.session_state[MESSAGES] = [Message(actor=ASSISTANT, payload="Chat history could not be loaded completely. How can I help you?")]
    
    # Mark as initialized to prevent reloading on next render
    st.session_state.initialized = True

# Initialize session state
init_session_state()

# Sidebar for chat selection
st.sidebar.header("Chat Sessions")
existing_chats = get_all_chat_sessions()
chat_options = ["New chat..."] + existing_chats

# Set the current selection in the dropdown based on session state
if not st.session_state.initialized:
    # First-time initialization or page reload
    if st.session_state[CURRENT_CHAT_KEY] in existing_chats:
        st.session_state[CHAT_SELECTION_KEY] = st.session_state[CURRENT_CHAT_KEY]
    else:
        st.session_state[CHAT_SELECTION_KEY] = "New chat..."

# Show the select box with the callback
st.sidebar.selectbox(
    "Select chat to load", 
    chat_options, 
    key=CHAT_SELECTION_KEY,
    on_change=on_chat_selected
)

# Main chat interface
st.title("ReZanAI")
st.write("Ask me about constitution of the Republic of Kazakhstan and I'll use RAG to answer your questions!")

# If we need to create a new chat on first load
if not st.session_state.initialized and st.session_state[CURRENT_CHAT_KEY] is None:
    on_chat_selected()

# Display messages
for msg in st.session_state[MESSAGES]:
    st.chat_message(msg.actor).write(msg.payload)

# Handle user input
prompt: str = st.chat_input("Enter a prompt here")
if prompt:
    # Add user message
    st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
    st.chat_message(USER).write(prompt)
    store_chat_message(st.session_state[CURRENT_CHAT_KEY], USER, prompt)
    
    # Generate and add AI response
    with st.spinner("Thinking..."):
        response: str = rag_pipeline(prompt)
    
    st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
    st.chat_message(ASSISTANT).write(response)
    store_chat_message(st.session_state[CURRENT_CHAT_KEY], ASSISTANT, response)









# import streamlit as st
# from dataclasses import dataclass
# from pipeline import rag_pipeline
# import uuid
# from common.models import Message
# from chroma.chroma import store_chat_message, load_chat_history, store_chat_session, get_all_chat_sessions
#
# USER = "user"
# ASSISTANT = "ai"
# MESSAGES = "messages"
#
# def init_session_state():
#     if "chat_id" not in st.session_state:
#         st.session_state.chat_id = None
#     if MESSAGES not in st.session_state:
#         st.session_state[MESSAGES] = []
#
# init_session_state()
#
# st.sidebar.header("Chat Sessions")
#
# existing_chats = get_all_chat_sessions()
# chat_options = ["New chat..."] + existing_chats
#
# # Determine index to select
# default_idx = 0
# if st.session_state.chat_id in existing_chats:
#     default_idx = chat_options.index(st.session_state.chat_id)
#
# selected_chat = st.sidebar.selectbox("Select chat to load", chat_options, index=default_idx)
#
# # Immediate reaction to selectbox change:
# if selected_chat == "New chat...":
#     # If no chat_id yet or different from previous, create new chat
#     if st.session_state.chat_id is None or st.session_state.chat_id != "new":
#         new_id = str(uuid.uuid4())
#         st.session_state.chat_id = new_id
#         st.session_state[MESSAGES] = [Message(actor=ASSISTANT, payload="Hi! How can I help you?")]
#         store_chat_session(new_id)
# else:
#     # Existing chat selected, load it if different
#     if st.session_state.chat_id != selected_chat:
#         st.session_state.chat_id = selected_chat
#         st.session_state[MESSAGES] = load_chat_history(selected_chat)
#
# st.title("ReZanAI")
# st.write("Ask me about constitution of the Republic of Kazakhstan and I'll use RAG to answer your questions!")
#
# for msg in st.session_state[MESSAGES]:
#     st.chat_message(msg.actor).write(msg.payload)
#
# prompt: str = st.chat_input("Enter a prompt here")
#
# if prompt:
#     st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
#     st.chat_message(USER).write(prompt)
#     store_chat_message(st.session_state.chat_id, "user", prompt)
#
#     with st.spinner("Thinking..."):
#         response: str = rag_pipeline(prompt)
#
#     st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
#     st.chat_message(ASSISTANT).write(response)
#     store_chat_message(st.session_state.chat_id, "ai", response)
#
#
#
#
#
