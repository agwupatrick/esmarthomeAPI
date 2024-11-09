# auth.py
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Union, Any, List, Tuple
from datetime import datetime, timedelta, timezone

import jwt
import re

# Only import config settings if needed
from .config import get_settings

settings = get_settings()


# Setup the password context using the bcrpt hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    else:
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expires.timestamp(),  # Encode expiration as Unix timestamp
        "sub": str(subject)
    }
    return jwt.encode(to_encode,settings.JWT_SECRET_KEY.get_secret_value(), algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    else:
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expires.timestamp(),  # Encode expiration as Unix timestamp
        "sub": str(subject)
    }
    return jwt.encode(to_encode,settings.JWT_REFRESH_SECRET_KEY.get_secret_value(), algorithm=settings.JWT_ALGORITHM)

def get_hashed_password(password: str) -> str:
    """
    Hashes the provided password using bycrpt algorithm.

    Args:
        password (str): The plain password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)

def verify_password(password: str, hashed_pass: str) -> bool:
    """
    Verifies the provided password against the hashed password.

    Args:
        password (str): The plain password.
        hashed_pass (str): The hashed password.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(password, hashed_pass)