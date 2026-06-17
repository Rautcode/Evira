"""Symmetric encryption for secrets stored at rest (config passwords).

Uses Fernet (AES). Key comes from CONFIG_ENCRYPTION_KEY (a urlsafe base64 32-byte
Fernet key); if unset, a stable key is derived from JWT_SECRET so encryption
works out of the box. Encrypted values are tagged with an `enc::` prefix so we
can detect them and remain backward-compatible with legacy plaintext configs.
"""
import os
import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)
_PREFIX = "enc::"
_fernet = None


def _get_fernet() -> Fernet:
    key = os.getenv("CONFIG_ENCRYPTION_KEY")
    if key:
        try:
            return Fernet(key.encode() if isinstance(key, str) else key)
        except Exception:
            logger.warning("CONFIG_ENCRYPTION_KEY is not a valid Fernet key; deriving from JWT_SECRET")
    secret = os.getenv("JWT_SECRET", "insecure-dev-secret")
    digest = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _inst() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = _get_fernet()
    return _fernet


def encrypt(value: str) -> str:
    """Encrypt a string; no-op for empty values or already-encrypted ones."""
    if not value or not isinstance(value, str) or value.startswith(_PREFIX):
        return value
    return _PREFIX + _inst().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """Decrypt an `enc::` value; pass through legacy plaintext unchanged."""
    if not isinstance(value, str) or not value.startswith(_PREFIX):
        return value
    try:
        return _inst().decrypt(value[len(_PREFIX):].encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt a stored secret (wrong CONFIG_ENCRYPTION_KEY / JWT_SECRET?)")
        return value
