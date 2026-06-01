from __future__ import annotations

from dataclasses import dataclass
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