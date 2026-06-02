from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AuditLogRecord:
	audit_id: str
	organization_id: str
	actor_user_id: str
	action: str
	resource_type: str
	resource_id: str | None
	result: str
	reason: str | None
	ip_address: str | None
	user_agent: str | None
	created_at: datetime
	floor_id: str | None = None