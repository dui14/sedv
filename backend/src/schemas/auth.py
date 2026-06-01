from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer, model_validator


class RequestPayload(BaseModel):
	model_config = ConfigDict(extra="forbid")

	@model_validator(mode="before")
	@classmethod
	def strip_strings(cls, value: object) -> object:
		if isinstance(value, dict):
			return {key: item.strip() if isinstance(item, str) else item for key, item in value.items()}
		return value


class AuthRegisterRequest(RequestPayload):
	email: str
	password: str
	full_name: str


class AuthLoginRequest(RequestPayload):
	email: str
	password: str


class AuthLogoutRequest(RequestPayload):
	reason: str | None = None


class AuthUserResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	user_id: str
	organization_id: str
	email: str
	full_name: str
	role: str
	status: str
	last_login_at: datetime | None = None
	created_at: datetime
	updated_at: datetime

	@field_serializer("last_login_at", "created_at", "updated_at")
	def serialize_datetime(self, value: datetime | None) -> str | None:
		if value is None:
			return None
		return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class AuthResponse(BaseModel):
	user: AuthUserResponse
	access_token: str
	token_type: str = "Bearer"
	expires_in: int = 1800


class SuccessResponse(BaseModel):
	success: bool = True