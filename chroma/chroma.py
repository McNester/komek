import chromadb
from datetime import datetime
import uuid
import json
import numpy as np
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from chromadb.config import Settings
from common.models import Message, User
import os

print("Starting chroma client")

llm_model = "nomic-embed-text"

chroma_client = chromadb.HttpClient(host="chroma", port=8000, settings=Settings(allow_reset=True, anonymized_telemetry=False))

class ChromaDBEmbeddingFunction:
    """
    Custom embedding function for ChromaDB using embeddings from Ollama.
    """
    def __init__(self, langchain_embeddings):
        self.langchain_embeddings = langchain_embeddings

    def __call__(self, input):
        print(f"Embedding input: {input[:1]}... total: {len(input)}")
        if isinstance(input, str):
            input = [input]

        embeddings = self.langchain_embeddings.embed_documents(input)
        print("Embedding complete.")

        numpy_embeddings = [np.array(embedding) for embedding in embeddings]
        return numpy_embeddings

embedding = ChromaDBEmbeddingFunction(
    OllamaEmbeddings(
        model=llm_model,
        base_url="http://host.docker.internal:11434"
    )
)


collection_name = "mental_health_support_collection"
collection = chroma_client.get_or_create_collection(
    name=collection_name,
    embedding_function=embedding
)

def add_documents_to_collection(documents, ids, metadatas, batch_size=5):
    print("Adding docs into the collections", flush=True)
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i + batch_size]
        batch_ids = ids[i:i + batch_size]
        batch_metadatas = metadatas[i:i + batch_size]
        print(f"Adding batch {i} to {i + len(batch_docs)}...", flush=True)

        collection.add(
            documents=batch_docs,
            metadatas=batch_metadatas,
            ids=batch_ids
        )
        print(f"Batch {i} to {i + len(batch_docs)} added", flush=True)

def initialize_collection(force_reload=False):
    """
    Initialize the collection with documents.
    Only loads if the collection is empty or if force_reload is True.
    
    Args:
        force_reload (bool): If True, will reload documents even if collection is not empty.
    """
    
    doc_count = collection.count()
    
    
    if doc_count > 0 and not force_reload:
        print(f"Collection already contains {doc_count} documents. Skipping initialization.")
        return
    
    
    json_file = "mental_health_docs.json"
    if not os.path.exists(json_file):
        print(f"Document file {json_file} not found. Skipping initialization.")
        return
    
    print(f"Opening {json_file}")
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        documents = data["documents"]
        metadatas = data["metadatas"]
        ids = data["ids"]
        
        add_documents_to_collection(documents, ids, metadatas)
        print(f"Added {len(documents)} mental health Q&A documents to collection.")
    except Exception as e:
        print(f"Error loading documents: {e}")



def create_user(username: str, password_hash: str, email: str = None) -> User:
    """
    Create a new user in the database.
    
    Args:
        username (str): Username
        password_hash (str): Hashed password
        email (str): User email (optional)
    
    Returns:
        User: The created user object
    """
    user_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    metadata = {
        "user_id": user_id,
        "username": username,
        "password_hash": password_hash,
        "email": email or "",
        "created_at": created_at,
        "type": "user"
    }
    
    collection.add(
        documents=[f"User: {username}"],
        metadatas=[metadata],
        ids=[f"user_{user_id}"]
    )
    
    print(f"Created user: {username} with ID: {user_id}")
    return User(user_id=user_id, username=username, email=email, created_at=created_at)

def get_user_by_username(username: str) -> tuple[User, str] | tuple[None, None]:
    """
    Retrieve a user by username.
    
    Args:
        username (str): Username to search for
    
    Returns:
        tuple: (User object, password_hash) or (None, None) if not found
    """
    try:
        results = collection.get(
            where={"$and": [{"username": username}, {"type": "user"}]}
        )
        
        metadatas = results.get("metadatas", [])
        if metadatas:
            meta = metadatas[0]
            user = User(
                user_id=meta.get("user_id"),
                username=meta.get("username"),
                email=meta.get("email"),
                created_at=meta.get("created_at")
            )
            return user, meta.get("password_hash")
        
        return None, None
    except Exception as e:
        print(f"Error getting user by username: {e}")
        return None, None

def get_user_by_id(user_id: str) -> User | None:
    """
    Retrieve a user by user_id.
    
    Args:
        user_id (str): User ID to search for
    
    Returns:
        User: User object or None if not found
    """
    try:
        results = collection.get(
            where={"$and": [{"user_id": user_id}, {"type": "user"}]}
        )
        
        metadatas = results.get("metadatas", [])
        if metadatas:
            meta = metadatas[0]
            return User(
                user_id=meta.get("user_id"),
                username=meta.get("username"),
                email=meta.get("email"),
                created_at=meta.get("created_at")
            )
        
        return None
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None

def username_exists(username: str) -> bool:
    """
    Check if a username already exists.
    
    Args:
        username (str): Username to check
    
    Returns:
        bool: True if username exists, False otherwise
    """
    user, _ = get_user_by_username(username)
    return user is not None





def create_session(user_id: str, session_token: str, expiry: str) -> bool:
    try:
        session_id = f"session_token_{session_token}"
        metadata = {
            "user_id": user_id,
            "session_token": session_token,
            "expiry": expiry,
            "created_at": datetime.utcnow().isoformat(),
            "type": "user_session"
        }
        collection.add(
            documents=[f"User session: {user_id}"],
            metadatas=[metadata],
            ids=[session_id]
        )
        print(f"Created session for user: {user_id}")
        return True
    except Exception as e:
        print(f"Error creating session: {e}")
        return False

def get_session(session_token: str) -> dict | None:
    try:
        results = collection.get(
            where={"$and": [{"session_token": session_token}, {"type": "user_session"}]}
        )
        metadatas = results.get("metadatas", [])
        if metadatas:
            session = metadatas[0]
            from common.auth import is_session_valid
            if not is_session_valid(session.get("expiry")):
                delete_session(session_token)
                return None
            return session
        return None
    except Exception as e:
        print(f"Error getting session: {e}")
        return None

def delete_session(session_token: str) -> bool:
    try:
        session_id = f"session_token_{session_token}"
        collection.delete(ids=[session_id])
        print(f"Deleted session: {session_token[:10]}...")
        return True
    except Exception as e:
        print(f"Error deleting session: {e}")
        return False

def delete_user_sessions(user_id: str) -> bool:
    try:
        results = collection.get(
            where={"$and": [{"user_id": user_id}, {"type": "user_session"}]}
        )
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            print(f"Deleted {len(ids_to_delete)} sessions for user: {user_id}")
        return True
    except Exception as e:
        print(f"Error deleting user sessions: {e}")
        return False

def cleanup_expired_sessions() -> int:
    try:
        results = collection.get(where={"type": "user_session"})
        metadatas = results.get("metadatas", [])
        ids = results.get("ids", [])
        from common.auth import is_session_valid
        expired_ids = []
        for metadata, session_id in zip(metadatas, ids):
            if not is_session_valid(metadata.get("expiry", "")):
                expired_ids.append(session_id)
        if expired_ids:
            collection.delete(ids=expired_ids)
            print(f"Cleaned up {len(expired_ids)} expired sessions")
        return len(expired_ids)
    except Exception as e:
        print(f"Error cleaning up expired sessions: {e}")
        return 0


def query_chromadb(query_text, n_results=3):
    """
    Query the ChromaDB collection for relevant documents.
    
    Args:
        query_text (str): The input query.
        n_results (int): The number of top results to return (default 3 for better context).
    
    Returns:
        list of dict: The top matching documents and their metadata.
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results["documents"], results["metadatas"]

def store_chat_message(chat_id, role, content, user_id):
    """Store a chat message with user association."""
    msg_id = str(uuid.uuid4())
    metadata = {
        "chat_id": chat_id,
        "user_id": user_id,
        "role": role,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "chat"
    }
    collection.add(
        documents=[content],
        metadatas=[metadata],
        ids=[msg_id]
    )

def load_chat_history(chat_id, user_id):
    """Load chat history for a specific chat and user."""
    results = collection.get(
        where={"$and": [{"chat_id": chat_id}, {"user_id": user_id}]}
    )

    metadatas = results.get("metadatas") or []
    documents = results.get("documents") or []

    if not metadatas or not documents:
        return []

    
    chat_items = [
        (meta, doc)
        for meta, doc in zip(metadatas, documents)
        if meta.get("type") == "chat"
    ]

    
    chat = sorted(
        chat_items,
        key=lambda x: x[0].get("timestamp") or datetime.min.isoformat()
    )

    return [Message(actor=("user" if meta["role"] == "user" else "ai"), payload=doc) for meta, doc in chat]

def store_chat_session(chat_id, user_id, chat_name="New Chat"):
    """
    Store a metadata record that represents the chat session with a name.
    """
    metadata = {
        "chat_id": chat_id,
        "user_id": user_id,
        "chat_name": chat_name,
        "type": "session",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    collection.add(
        documents=[f"Chat session: {chat_name}"],
        metadatas=[metadata],
        ids=[f"session_{chat_id}"]
    )

def update_chat_name(chat_id, new_name):
    """
    Update the name of an existing chat session.
    """
    try:
        session_id = f"session_{chat_id}"
        
        results = collection.get(ids=[session_id])
        if not results.get("metadatas"):
            print(f"Session {chat_id} not found")
            return
        
        existing_meta = results["metadatas"][0]
        user_id = existing_meta.get("user_id")
        
        
        collection.delete(ids=[session_id])
        
        
        metadata = {
            "chat_id": chat_id,
            "user_id": user_id,
            "chat_name": new_name,
            "type": "session",
            "updated_at": datetime.utcnow().isoformat()
        }
        collection.add(
            documents=[f"Chat session: {new_name}"],
            metadatas=[metadata],
            ids=[session_id]
        )
        print(f"Updated chat name to: {new_name}")
    except Exception as e:
        print(f"Error updating chat name: {e}")

def get_all_chat_sessions(user_id):
    """
    Retrieve all chat sessions for a specific user, sorted by most recent first.
    Returns list of tuples: (chat_id, chat_name, updated_at)
    """
    results = collection.get(where={"$and": [{"type": "session"}, {"user_id": user_id}]})

    sessions = []
    metadatas = results.get("metadatas") or []
    
    for meta in metadatas:
        chat_id = meta.get("chat_id")
        chat_name = meta.get("chat_name", "Untitled Chat")
        updated_at = meta.get("updated_at", meta.get("created_at", ""))
        
        if chat_id:
            sessions.append((chat_id, chat_name, updated_at))
    
    
    sessions.sort(key=lambda x: x[2], reverse=True)
    
    return sessions

def delete_chat_session(chat_id, user_id):
    """
    Delete a chat session and all its messages for a specific user.
    """
    try:
        
        results = collection.get(where={"$and": [{"chat_id": chat_id}, {"user_id": user_id}]})
        ids_to_delete = results.get("ids", [])
        
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            print(f"Deleted chat {chat_id} with {len(ids_to_delete)} items")
            return True
    except Exception as e:
        print(f"Error deleting chat: {e}")
        return False

def get_chat_name(chat_id):
    """
    Get the name of a chat session.
    """
    try:
        results = collection.get(
            where={"$and": [{"chat_id": chat_id}, {"type": "session"}]}
        )
        metadatas = results.get("metadatas", [])
        if metadatas:
            return metadatas[0].get("chat_name", "Untitled Chat")
    except Exception as e:
        print(f"Error getting chat name: {e}")
    return "Untitled Chat"


initialize_collection()
