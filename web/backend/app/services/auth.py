import json
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from ..config import Settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user_id: str, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "type": "access", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: Settings) -> dict:
    """Decode and validate a JWT. Raises JWTError on failure."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def encrypt_credentials(data: dict, key: str) -> str:
    from cryptography.fernet import Fernet

    f = Fernet(key.encode())
    return f.encrypt(json.dumps(data).encode()).decode()


def decrypt_credentials(encrypted: str, key: str) -> dict:
    from cryptography.fernet import Fernet

    f = Fernet(key.encode())
    return json.loads(f.decrypt(encrypted.encode()).decode())
