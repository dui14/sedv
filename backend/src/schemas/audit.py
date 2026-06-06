from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, field_serializer


class AuditLogItemResponse(BaseModel):
	audit_id: str
	organization_id: str
	actor_user_id: str
	actor_name: str
	actor_floor_name: str | None = None
	actor_department: str | None = None
	action: str
	resource_type: str
	resource_id: str | None
	result: Literal["success", "denied", "error"]
	reason: str | None = None
	created_at: datetime

	@field_serializer("created_at")
	def serialize_datetime(self, value: datetime) -> str:
		return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class AuditLogListResponse(BaseModel):
	items: list[AuditLogItemResponse]
	page: int
	page_size: int
	total: int
