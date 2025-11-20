"""
Common module for shared models and authentication.
"""

from .models import Message, User
from .auth import (
    hash_password,
    verify_password,
    validate_username,
    validate_password,
    generate_user_id
)
