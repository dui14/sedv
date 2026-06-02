from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class UserRecord:
	user_id: str
	organization_id: str
	email: str
	full_name: str
	password_hash: str | None
	role: str
	status: str
	last_login_at: datetime | None
	created_at: datetime
	updated_at: datetime
	floor_id: str | None = field(default=None)
	floor_name: str | None = field(default=None)
	pending_floor_id: str | None = field(default=None)
	pending_floor_name: str | None = field(default=None)
	manager_id: str | None = field(default=None)