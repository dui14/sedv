from __future__ import annotations

from enum import Enum


class Role(str, Enum):
	COMPANY = "company"
	ADMIN = "admin"
	MANAGER = "manager"
	USER = "user"