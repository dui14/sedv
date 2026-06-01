from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def derive_file_key(seed: str) -> bytes:
	return hashlib.sha256(seed.encode("utf-8")).digest()


def encrypt_bytes(plaintext: bytes, key: bytes) -> tuple[bytes, str]:
	nonce = os.urandom(12)
	encrypted = AESGCM(key).encrypt(nonce, plaintext, None)
	return encrypted, base64.urlsafe_b64encode(nonce).decode("ascii")


def decrypt_bytes(ciphertext: bytes, key: bytes, iv: str) -> bytes:
	nonce = base64.urlsafe_b64decode(iv.encode("ascii"))
	return AESGCM(key).decrypt(nonce, ciphertext, None)