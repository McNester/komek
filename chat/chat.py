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
    create_user,
    get_user_by_username,
    username_exists,
    get_user_by_id,
    username_exists,
    create_session,
    get_session,
    delete_session,
    delete_user_sessions
)
from ollama_client.llm import query_ollama
from common.auth import (
    hash_password,
    verify_password,
    validate_username,
    validate_password,
    generate_session_token,
    get_session_expiry,
)

USER = "user"
ASSISTANT = "ai"
MESSAGES = "messages"
CURRENT_CHAT_KEY = "chat_id"
CURRENT_CHAT_NAME = "chat_name"
CURRENT_USER = "current_user"
USER_ID = "user_id"
IS_AUTHENTICATED = "is_authenticated"
SESSION_TOKEN = "session_token"
SESSION_CHECKED = "session_checked"


st.set_page_config(page_title="Mental Health Support", layout="wide")


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
    if SESSION_CHECKED not in st.session_state:
        st.session_state[SESSION_CHECKED] = False
    
    if IS_AUTHENTICATED not in st.session_state:
        st.session_state[IS_AUTHENTICATED] = False
    if CURRENT_USER not in st.session_state:
        st.session_state[CURRENT_USER] = None
    if USER_ID not in st.session_state:
        st.session_state[USER_ID] = None
    if SESSION_TOKEN not in st.session_state:
        st.session_state[SESSION_TOKEN] = None
    if CURRENT_CHAT_KEY not in st.session_state:
        st.session_state[CURRENT_CHAT_KEY] = None
    if CURRENT_CHAT_NAME not in st.session_state:
        st.session_state[CURRENT_CHAT_NAME] = None
    if MESSAGES not in st.session_state:
        st.session_state[MESSAGES] = []
    if "chat_list_refresh" not in st.session_state:
        st.session_state.chat_list_refresh = 0
    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "login"

    if not st.session_state[SESSION_CHECKED] and not st.session_state[IS_AUTHENTICATED]:
        check_existing_session()
        st.session_state[SESSION_CHECKED] = True


def check_existing_session():
    """
    Check if there's a valid session token and restore the user session.
    This runs once per page load.
    """
    
    try:
        query_params = st.query_params
        token = query_params.get("st", None)  
        
        if token:
            
            session_data = get_session(token)
            
            if session_data:
                
                user_id = session_data.get("user_id")
                user = get_user_by_id(user_id)
                
                if user:
                    st.session_state[IS_AUTHENTICATED] = True
                    st.session_state[CURRENT_USER] = user.username
                    st.session_state[USER_ID] = user.user_id
                    st.session_state[SESSION_TOKEN] = token
                    print(f"Session restored for user: {user.username}")
                    return True
            else:
                
                st.query_params.clear()
        
        return False
    except Exception as e:
        print(f"Error checking existing session: {e}")
        return False



def login_user(username, password):
    """
    Authenticate a user and create a session.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    user, password_hash = get_user_by_username(username)
    
    if user is None:
        return False, "Username not found"
    
    if not verify_password(password, password_hash):
        return False, "Incorrect password"
    
    
    session_token = generate_session_token()
    expiry = get_session_expiry(days=7)  
    
    
    if create_session(user.user_id, session_token, expiry):
        
        st.session_state[IS_AUTHENTICATED] = True
        st.session_state[CURRENT_USER] = username
        st.session_state[USER_ID] = user.user_id
        st.session_state[SESSION_TOKEN] = session_token
        
        
        st.query_params["st"] = session_token
        
        return True, "Login successful"
    else:
        return False, "Error creating session"

def register_user(username, password, email=None):
    """
    Register a new user and create a session.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        return False, error_msg
    
    
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return False, error_msg
    
    
    if username_exists(username):
        return False, "Username already exists"
    
    
    password_hash = hash_password(password)
    user = create_user(username, password_hash, email)
    
    
    session_token = generate_session_token()
    expiry = get_session_expiry(days=7)
    
    
    if create_session(user.user_id, session_token, expiry):
        
        st.session_state[IS_AUTHENTICATED] = True
        st.session_state[CURRENT_USER] = username
        st.session_state[USER_ID] = user.user_id
        st.session_state[SESSION_TOKEN] = session_token
        
        
        st.query_params["st"] = session_token
        
        return True, "Registration successful"
    else:
        return False, "Error creating session"

def logout_user():
    """Log out the current user and clear session."""
    
    if st.session_state.get(SESSION_TOKEN):
        delete_session(st.session_state[SESSION_TOKEN])
    
    
    st.session_state[IS_AUTHENTICATED] = False
    st.session_state[CURRENT_USER] = None
    st.session_state[USER_ID] = None
    st.session_state[SESSION_TOKEN] = None
    st.session_state[CURRENT_CHAT_KEY] = None
    st.session_state[CURRENT_CHAT_NAME] = None
    st.session_state[MESSAGES] = []
    st.session_state[SESSION_CHECKED] = False
    
    
    st.query_params.clear()
    
    st.rerun()

def show_login_page():
    """Display the login page."""
    st.title("Mental Health Support")
    st.subheader("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                success, message = login_user(username, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("Don't have an account?")
    with col2:
        if st.button("Register"):
            st.session_state.auth_page = "register"
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_register_page():
    """Display the registration page."""
    st.title("Mental Health Support")
    st.subheader("Register")
    
    with st.form("register_form"):
        username = st.text_input("Username", help="3-20 characters, letters, numbers, hyphens, and underscores only")
        email = st.text_input("Email (optional)")
        password = st.text_input("Password", type="password", help="Minimum 6 characters")
        password_confirm = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("Username and password are required")
            elif password != password_confirm:
                st.error("Passwords do not match")
            else:
                success, message = register_user(username, password, email)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("Already have an account?")
    with col2:
        if st.button("Login"):
            st.session_state.auth_page = "login"
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

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
        
        chat_name = chat_name.strip('"').strip("'")
        
        if len(chat_name) > 50:
            chat_name = chat_name[:47] + "..."
        return chat_name
    except Exception as e:
        print(f"Error generating chat name: {e}")
        
        words = first_message.split()[:4]
        return " ".join(words) + ("..." if len(first_message.split()) > 4 else "")

def create_new_chat():
    """Create a new chat session."""
    new_id = str(uuid.uuid4())
    st.session_state[CURRENT_CHAT_KEY] = new_id
    st.session_state[CURRENT_CHAT_NAME] = "New Chat"
    st.session_state[MESSAGES] = []
    
    store_chat_session(new_id, st.session_state[USER_ID], "New Chat")
    st.session_state.chat_list_refresh += 1
    st.rerun()

def load_chat(chat_id, chat_name):
    """Load an existing chat."""
    if chat_id != st.session_state[CURRENT_CHAT_KEY]:
        st.session_state[CURRENT_CHAT_KEY] = chat_id
        st.session_state[CURRENT_CHAT_NAME] = chat_name
        loaded_messages = load_chat_history(chat_id, st.session_state[USER_ID])
        st.session_state[MESSAGES] = loaded_messages if loaded_messages else []
        st.rerun()

def delete_current_chat():
    """Delete the current chat and switch to a new one."""
    if st.session_state[CURRENT_CHAT_KEY]:
        delete_chat_session(st.session_state[CURRENT_CHAT_KEY], st.session_state[USER_ID])
        st.session_state.chat_list_refresh += 1
        create_new_chat()


init_session_state()


if not st.session_state[IS_AUTHENTICATED]:
    if st.session_state.auth_page == "login":
        show_login_page()
    else:
        show_register_page()
    st.stop()




with st.sidebar:
    
    st.markdown(f"### {st.session_state[CURRENT_USER]}")
    if st.button("Logout", type="secondary", use_container_width=True):
        logout_user()
    
    st.divider()
    st.title("Support Sessions")
    
    
    if st.button("+ New Session", type="primary", use_container_width=True):
        create_new_chat()
    
    st.divider()
    
    
    chat_sessions = get_all_chat_sessions(st.session_state[USER_ID])
    
    if chat_sessions:
        st.subheader("Previous Sessions")
        
        
        for chat_id, chat_name, updated_at in chat_sessions:
            
            is_active = (chat_id == st.session_state[CURRENT_CHAT_KEY])
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                
                if st.button(
                    f"{'> ' if is_active else ''}{chat_name}",
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                    type="secondary" if is_active else "tertiary"
                ):
                    load_chat(chat_id, chat_name)
            
            with col2:
                
                if st.button("❌", key=f"delete_{chat_id}", help="Delete this session"):
                    if chat_id == st.session_state[CURRENT_CHAT_KEY]:
                        delete_current_chat()
                    else:
                        delete_chat_session(chat_id, st.session_state[USER_ID])
                        st.session_state.chat_list_refresh += 1
                        st.rerun()
    else:
        st.info("No previous sessions. Start a new conversation.")


st.title("Mental Health Support Assistant")


if st.session_state[CURRENT_CHAT_NAME] and st.session_state[CURRENT_CHAT_NAME] != "New Chat":
    st.caption(f"Session: {st.session_state[CURRENT_CHAT_NAME]}")

st.write("Share what's on your mind. I'm here to listen and provide supportive guidance.")


if st.session_state[CURRENT_CHAT_KEY] is None:
    create_new_chat()


for msg in st.session_state[MESSAGES]:
    with st.chat_message(msg.actor):
        st.write(msg.payload)


prompt = st.chat_input("How are you feeling today?")

if prompt:
    
    is_first_message = (
        len(st.session_state[MESSAGES]) == 0 and 
        st.session_state[CURRENT_CHAT_NAME] == "New Chat"
    )
    
    
    st.session_state[MESSAGES].append(Message(actor=USER, payload=prompt))
    with st.chat_message(USER):
        st.write(prompt)
    
    
    store_chat_message(st.session_state[CURRENT_CHAT_KEY], USER, prompt, st.session_state[USER_ID])
    
    
    if is_first_message:
        with st.spinner("Creating session..."):
            chat_name = generate_chat_name(prompt)
            st.session_state[CURRENT_CHAT_NAME] = chat_name
            update_chat_name(st.session_state[CURRENT_CHAT_KEY], chat_name)
            st.session_state.chat_list_refresh += 1
    
    
    with st.spinner("Thinking..."):
        response = rag_pipeline(prompt)
    
    st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
    with st.chat_message(ASSISTANT):
        st.write(response)
    
    
    store_chat_message(st.session_state[CURRENT_CHAT_KEY], ASSISTANT, response, st.session_state[USER_ID])
    
    
    if is_first_message:
        st.rerun()
