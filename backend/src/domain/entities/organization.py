from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class OrganizationRecord:
	organization_id: str
	name: str
	slug: str
	created_at: datetime
	updated_at: datetime