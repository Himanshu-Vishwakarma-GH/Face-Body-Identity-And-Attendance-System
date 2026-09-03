import time
import base64
import os
import bcrypt
import jwt
from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.config import settings
from backend.models import User, UserRole

security_bearer = HTTPBearer(auto_error=False)

# --- Password Hashing & Verification (bcrypt) ---

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

# --- JWT Token Generation & Verification ---

def create_access_token(data: Dict[str, Any], expires_delta_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire_minutes = expires_delta_minutes or settings.JWT_EXPIRATION_MINUTES
    expire_ts = time.time() + (expire_minutes * 60)
    to_encode.update({
        "exp": int(expire_ts),
        "iat": int(time.time()),
        "iss": "ai-access-system"
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

# --- AES-256-GCM Encryption / Decryption for Embeddings at Rest ---

def encrypt_embedding(embedding_bytes: bytes) -> str:
    """Encrypts embedding bytes using AES-256-GCM and returns a base64 encoded string with nonce."""
    key = settings.get_aes_key_bytes()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
    ciphertext = aesgcm.encrypt(nonce, embedding_bytes, None)
    # Combine nonce + ciphertext and base64-encode
    return base64.b64encode(nonce + ciphertext).decode("utf-8")

def decrypt_embedding(encrypted_base64: str) -> bytes:
    """Decrypts a base64 encoded AES-256-GCM ciphertext back into raw embedding bytes."""
    key = settings.get_aes_key_bytes()
    aesgcm = AESGCM(key)
    data = base64.b64decode(encrypted_base64)
    nonce = data[:12]
    ciphertext = data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)

# --- FastAPI RBAC Dependencies ---

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    role_str: str = payload.get("role", "admin")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        role = UserRole(role_str)
    except ValueError:
        role = UserRole.ADMIN

    return User(
        username=username,
        role=role,
        email=payload.get("email"),
        is_active=True
    )

def require_roles(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires one of {[r.value for r in allowed_roles]} roles"
            )
        return current_user
    return role_checker
