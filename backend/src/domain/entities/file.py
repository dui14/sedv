from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class FileRecord:
	file_id: str
	organization_id: str
	owner_user_id: str
	uploaded_by_user_id: str
	original_name: str
	storage_name: str
	storage_path: str
	mime_type: str
	size_bytes: int
	sha256: str
	encryption_algorithm: str
	encryption_iv: str
	encryption_key_version: str
	vault_type: str
	publish_status: str
	reviewed_by_user_id: str | None
	reviewed_at: datetime | None
	review_note: str | None
	status: str
	deleted_at: datetime | None
	created_at: datetime
	updated_at: datetime
	floor_id: str | None = None


@dataclass(slots=True)
class PublishRequestRecord:
	request_id: str
	organization_id: str
	file_id: str
	requester_user_id: str
	target: str
	status: str
	reviewed_by_user_id: str | None
	reviewed_at: datetime | None
	review_note: str | None
	created_at: datetime
	updated_at: datetime