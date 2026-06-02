from __future__ import annotations

from enum import Enum


class Status(str, Enum):
	ACTIVE = "active"
	DISABLED = "disabled"
	PENDING = "pending"


class VaultType(str, Enum):
	FLOOR = "floor"
	COMPANY = "company"
	PRIVATE = "private"


class PublishStatus(str, Enum):
	PENDING = "pending"
	PUBLISHED = "published"
	REJECTED = "rejected"
	NOT_APPLICABLE = "na"


class RequestStatus(str, Enum):
	PENDING = "pending"
	APPROVED = "approved"
	REJECTED = "rejected"