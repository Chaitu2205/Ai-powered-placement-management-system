"""
Password hashing.

Uses passlib's bcrypt backend. Passwords are never stored or logged in
plaintext anywhere in the application - only `password_hash` is persisted.
"""
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored hash."""
    return _pwd_context.verify(plain_password, password_hash)
