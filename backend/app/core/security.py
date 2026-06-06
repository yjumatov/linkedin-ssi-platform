"""Credential encryption utilities using Fernet symmetric encryption."""
from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    key = os.environ.get("ENCRYPTION_KEY", "")
    if not key:
        key = Fernet.generate_key().decode()
    # Ensure the key is valid base64 32-byte Fernet key
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        # Derive a valid key from whatever was provided
        padded = (key + "=" * (44 - len(key) % 44))[:44]
        return Fernet(padded.encode())


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value and return base64-encoded ciphertext."""
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext back to plaintext."""
    fernet = _get_fernet()
    try:
        return fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt value — invalid key or corrupted data")


def generate_fernet_key() -> str:
    """Generate a new valid Fernet key (use once, store in env)."""
    return Fernet.generate_key().decode()
