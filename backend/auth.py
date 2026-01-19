# auth.py - Authentication utilities

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from models import User
import hashlib
import bcrypt

# Secret key for JWT - In production, use environment variable
SECRET_KEY = "your-secret-key-change-in-production-minimum-32-characters-long"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Password hashing - Use bcrypt directly to avoid passlib initialization issues

# Configure bcrypt
BCRYPT_ROUNDS = 12


def _prepare_password(password: str) -> bytes:
    """Prepare password for bcrypt. If > 72 bytes, pre-hash with SHA-256."""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Pre-hash long passwords with SHA-256 to get a fixed 64-char hex string (32 bytes when decoded)
        # Then bcrypt will hash this shorter value
        sha256_hash = hashlib.sha256(password_bytes).hexdigest()
        return sha256_hash.encode('utf-8')
    return password_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly."""
    try:
        password_bytes = _prepare_password(plain_password)
        # Convert hashed_password string to bytes if needed
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly. Long passwords (>72 bytes) are pre-hashed with SHA-256."""
    password_bytes = _prepare_password(password)
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()

