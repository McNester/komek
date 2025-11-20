"""
Authentication module for user management.
Handles user registration, login, and session management.
"""
import bcrypt
import uuid
from datetime import datetime, timedelta
import secrets

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password (str): Plain text password
    
    Returns:
        str: Hashed password
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password (str): Plain text password
        hashed_password (str): Hashed password to compare against
    
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def generate_user_id() -> str:
    """
    Generate a unique user ID.
    
    Returns:
        str: UUID for the user
    """
    return str(uuid.uuid4())

def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format.
    
    Args:
        username (str): Username to validate
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 20:
        return False, "Username must be at most 20 characters long"
    
    if not username.replace('_', '').replace('-', '').isalnum():
        return False, "Username can only contain letters, numbers, hyphens, and underscores"
    
    return True, ""

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password (str): Password to validate
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if len(password) > 100:
        return False, "Password is too long"
    
    return True, ""



def generate_session_token() -> str:
    return secrets.token_urlsafe(32)

def get_session_expiry(days: int = 7) -> str:
    expiry = datetime.utcnow() + timedelta(days=days)
    return expiry.isoformat()

def is_session_valid(expiry_str: str) -> bool:
    try:
        expiry = datetime.fromisoformat(expiry_str)
        return datetime.utcnow() < expiry
    except Exception:
        return False

