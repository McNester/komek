import streamlit as st
from dataclasses import dataclass
from pipeline import rag_pipeline
import uuid
from common.models import Message
from chroma.chroma import (
    store_chat_message, 
    load_chat_history, 
    store_chat_session, 
    get_all_chat_sessions,
    update_chat_name,
    delete_chat_session,
    get_chat_name
)
from ollama_client.llm import query_ollama

USER = "user"
ASSISTANT = "ai"
MESSAGES = "messages"
CURRENT_CHAT_KEY = "chat_id"
CURRENT_CHAT_NAME = "chat_name"

# Page config
st.set_page_config(page_title="Mental Health Support", page_icon="🧠", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .chat-item {
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .chat-item:hover {
        background-color: #f0f2f6;
    }
    .chat-item-active {
        background-color: #e8eaf0;
        font-weight: bold;
    }
    .stButton button {
        width: 100%;
    }
    .crisis-info {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize all required session state variables."""
    if CURRENT_CHAT_KEY not in st.session_state:
        st.session_state[CURRENT_CHAT_KEY] = None
    if CURRENT_CHAT_NAME not in st.session_state:
        st.session_state[CURRENT_CHAT_NAME] = None
    if MESSAGES not in st.session_state:
        st.session_state[MESSAGES] = []
    if "chat_list_refresh" not in st.session_state:
        st.session_state.chat_list_refresh = 0

def generate_chat_name(first_message):
    """
    Generate a short, descriptive chat name from the first user message.
    Uses the LLM to create a concise title (max 4 words).
    """
    try:
        prompt = f"""Generate a very short title (maximum 4 words) for a mental health support conversation that starts with this:
"{first_message}"

Reply with ONLY the title, nothing else. Keep it concise, empathetic and professional.
Example: "Anxiety and Sleep Issues" or "Depression Support"
Title:"""
        
        chat_name = query_ollama(prompt).strip()
        # Remove quotes if present
        chat_name = chat_name.strip('"').strip("'")
        # Limit to 50 characters
        if len(chat_name) > 50:
            chat_name = chat_name[:47] + "..."
        return chat_name
    except Exception as e:
        print(f"Error generating chat name: {e}")
        # Fallback: use first few words of the message
        words = first_message.split()[:4]
        return " ".join(words) + ("..." if len(first_message.split()) > 4 else "")

def create_new_chat():
    """Create a new chat session."""
    new_id = str(uuid.uuid4())
    st.session_state[CURRENT_CHAT_KEY] = new_id
    st.session_state[CURRENT_CHAT_NAME] = "New Chat"
    st.session_state[MESSAGES] = []
    # Store session with temporary name
    store_chat_session(new_id, "New Chat")
    st.session_state.chat_list_refresh += 1
    st.rerun()

def load_chat(chat_id, chat_name):
    """Load an existing chat."""
    if chat_id != st.session_state[CURRENT_CHAT_KEY]:
        st.session_state[CURRENT_CHAT_KEY] = chat_id
        st.session_state[CURRENT_CHAT_NAME] = chat_name
        loaded_messages = load_chat_history(chat_id)
        st.session_state[MESSAGES] = loaded_messages if loaded_messages else []
        st.rerun()

def delete_current_chat():
    """Delete the current chat and switch to a new one."""
    if st.session_state[CURRENT_CHAT_KEY]:
        delete_chat_session(st.session_state[CURRENT_CHAT_KEY])
        st.session_state.chat_list_refresh += 1
        create_new_chat()

# Initialize session state
init_session_state()

# Sidebar
with st.sidebar:
    st.title("Support Sessions")
    
    # # Crisis resources
    # with st.expander("Crisis Resources", expanded=False):
    #     st.markdown("""
    #     **If you're in crisis:**
    #     
    #     - National Suicide Prevention Lifeline: 988
    #     - Crisis Text Line: Text HOME to 741741
    #     - International: findahelpline.com
    #     
    #     This is an AI support tool, not a replacement for professional help.
    #     """)
    
    # New Chat button
    if st.button("+ New Session", type="primary", use_container_width=True):
        create_new_chat()
    
    st.divider()
    
    # Get all chat sessions
    chat_sessions = get_all_chat_sessions()
    
    if chat_sessions:
        st.subheader("Previous Sessions")
        
        # Display each chat as a clickable item
        for chat_id, chat_name, updated_at in chat_sessions:
            # Check if this is the active chat
            is_active = (chat_id == st.session_state[CURRENT_CHAT_KEY])
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Make chat name clickable
                if st.button(
                    f"{'> ' if is_active else ''}{chat_name}",
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                    type="secondary" if is_active else "tertiary"
                ):
                    load_chat(chat_id, chat_name)
            
            with col2:
                # Delete button
                if st.button("X", key=f"delete_{chat_id}", help="Delete this session"):
                    if chat_id == st.session_state[CURRENT_CHAT_KEY]:
                        delete_current_chat()
                    else:
                        delete_chat_session(chat_id)
                        st.session_state.chat_list_refresh += 1
                        st.rerun()
    else:
        st.info("No previous sessions. Start a new conversation.")

# Main chat interface
st.title("Mental Health Support Assistant")

# Display current chat name if exists
if st.session_state[CURRENT_CHAT_NAME] and st.session_state[CURRENT_CHAT_NAME] != "New Chat":
    st.caption(f"Session: {st.session_state[CURRENT_CHAT_NAME]}")

st.write("Share what's on your mind. I'm here to listen and provide supportive guidance.")

# Create new chat if none exists
if st.session_state[CURRENT_CHAT_KEY] is None:
    create_new_chat()

# Display messages
for msg in st.session_state[MESSAGES]:
    with st.chat_message(msg.actor):
        st.write(msg.payload)

# Handle user input
prompt = st.chat_input("How are you feeling today?")

if prompt:
    # Check if this is the first message in a new chat
    is_first_message = (
        len(st.session_state[MESSAGES]) == 0 and 
        st.session_state[CURRENT_CHAT_NAME] == "New Chat"
    )
    
    # Add user message
    st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
    with st.chat_message(USER):
        st.write(prompt)
    
    # Store user message
    store_chat_message(st.session_state[CURRENT_CHAT_KEY], USER, prompt)
    
    # Generate chat name from first message
    if is_first_message:
        with st.spinner("Creating session..."):
            chat_name = generate_chat_name(prompt)
            st.session_state[CURRENT_CHAT_NAME] = chat_name
            update_chat_name(st.session_state[CURRENT_CHAT_KEY], chat_name)
            st.session_state.chat_list_refresh += 1
    
    # Generate and add AI response
    with st.spinner("Thinking..."):
        response = rag_pipeline(prompt)
    
    st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
    with st.chat_message(ASSISTANT):
        st.write(response)
    
    # Store AI message
    store_chat_message(st.session_state[CURRENT_CHAT_KEY], ASSISTANT, response)
    
    # Rerun to update UI with new chat name
    if is_first_message:
        st.rerun()
