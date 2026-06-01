from __future__ import annotations

import secrets


def new_id() -> str:
	return secrets.token_hex(16)


def new_jti() -> str:
	return secrets.token_hex(16)