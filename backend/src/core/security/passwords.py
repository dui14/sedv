from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


HASH_NAME = "sha256"
ITERATIONS = 210000
SALT_BYTES = 16


def hash_password(password: str) -> str:
	salt = secrets.token_bytes(SALT_BYTES)
	derived = hashlib.pbkdf2_hmac(HASH_NAME, password.encode("utf-8"), salt, ITERATIONS)
	return "pbkdf2_sha256${iterations}${salt}${hash}".format(
		iterations=ITERATIONS,
		salt=base64.urlsafe_b64encode(salt).decode("ascii"),
		hash=base64.urlsafe_b64encode(derived).decode("ascii"),
	)


def verify_password(password: str, password_hash: str) -> bool:
	try:
		algorithm, iterations, salt_b64, hash_b64 = password_hash.split("$", 3)
	except ValueError:
		return False
	if algorithm != "pbkdf2_sha256":
		return False
	try:
		salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
		expected = base64.urlsafe_b64decode(hash_b64.encode("ascii"))
		rounds = int(iterations)
	except (ValueError, TypeError):
		return False
	derived = hashlib.pbkdf2_hmac(HASH_NAME, password.encode("utf-8"), salt, rounds)
	return hmac.compare_digest(derived, expected)