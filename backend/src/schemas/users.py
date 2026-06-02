from __future__ import annotations

from datetime import timezone

from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import datetime


class UserItemResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	user_id: str
	organization_id: str
	email: str
	full_name: str
	role: str
	status: str
	floor_id: str | None = None
	floor_name: str | None = None
	pending_floor_id: str | None = None
	pending_floor_name: str | None = None
	manager_id: str | None = None
	last_login_at: datetime | None = None
	created_at: datetime
	updated_at: datetime

	@field_serializer("last_login_at", "created_at", "updated_at")
	def serialize_datetime(self, value: datetime | None) -> str | None:
		if value is None:
			return None
		return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class UserListResponse(BaseModel):
	items: list[UserItemResponse]
	page: int
	page_size: int
	total: int


class CreateUserRequest(BaseModel):
	model_config = ConfigDict(extra="forbid")
	email: str
	full_name: str
	password: str
	role: str = "user"
	floor_id: str | None = None


class UpdateUserRequest(BaseModel):
	model_config = ConfigDict(extra="forbid")
	email: str | None = None
	full_name: str | None = None
	password: str | None = None
	role: str | None = None
	status: str | None = None
	floor_id: str | None = None


class FloorItemResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)
	floor_id: str
	organization_id: str
	name: str
	slug: str


class FloorListResponse(BaseModel):
	items: list[FloorItemResponse]
