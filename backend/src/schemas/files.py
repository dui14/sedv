from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer


class FileItemResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	file_id: str
	organization_id: str
	owner_user_id: str
	owner_name: str
	uploaded_by_user_id: str
	original_name: str
	mime_type: str
	size_bytes: int
	sha256: str
	encryption_algorithm: Literal["AES-256-GCM"]
	vault_type: Literal["floor", "company", "private"]
	publish_status: Literal["pending", "published", "rejected", "na"]
	floor_id: str | None = None
	reviewed_by_user_id: str | None = None
	reviewed_at: datetime | None = None
	review_note: str | None = None
	status: Literal["active", "deleted", "quarantined"]
	created_at: datetime
	updated_at: datetime
	deleted_at: datetime | None = None

	@field_serializer("created_at", "updated_at", "deleted_at", "reviewed_at")
	def serialize_datetime(self, value: datetime | None) -> str | None:
		if value is None:
			return None
		return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class FileListResponse(BaseModel):
	items: list[FileItemResponse]
	page: int
	page_size: int
	total: int


class FileDeleteResponse(BaseModel):
	success: bool = True
	deleted_file_id: str


class FileApproveRequest(BaseModel):
	model_config = ConfigDict(extra="forbid")
	note: str | None = None


class FileRejectRequest(BaseModel):
	model_config = ConfigDict(extra="forbid")
	note: str | None = None


class FileAdminUpdateRequest(BaseModel):
	model_config = ConfigDict(extra="forbid")
	original_name: str | None = None
	vault_type: Literal["floor", "company", "private"] | None = None
	publish_status: Literal["pending", "published", "rejected", "na"] | None = None
	status: Literal["active", "deleted", "quarantined"] | None = None


class RequestPublishRequest(BaseModel):
	model_config = ConfigDict(extra="forbid")
	target: Literal["floor", "company"]


class PublishRequestResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	request_id: str
	organization_id: str
	file_id: str
	file_name: str
	requester_user_id: str
	requester_name: str
	target: Literal["floor", "company"]
	status: Literal["pending", "approved", "rejected"]
	reviewed_by_user_id: str | None = None
	reviewed_at: datetime | None = None
	review_note: str | None = None
	created_at: datetime
	updated_at: datetime

	@field_serializer("reviewed_at", "created_at", "updated_at")
	def serialize_datetime(self, value: datetime | None) -> str | None:
		if value is None:
			return None
		return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class PublishRequestListResponse(BaseModel):
	items: list[PublishRequestResponse]
	total: int
