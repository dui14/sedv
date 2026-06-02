from __future__ import annotations

import re

from ...domain.entities.audit_log import AuditLogRecord
from ...utils.datetime import ensure_utc
from .client import MongoDatabaseClient
from .collections import AUDIT_LOGS_COLLECTION

try:
	from pymongo import DESCENDING
except ImportError:  # pragma: no cover - dependency is validated at startup
	DESCENDING = -1


def _audit_log_to_document(record: AuditLogRecord) -> dict:
	return {
		"_id": record.audit_id,
		"organization_id": record.organization_id,
		"actor_user_id": record.actor_user_id,
		"floor_id": record.floor_id,
		"action": record.action,
		"resource_type": record.resource_type,
		"resource_id": record.resource_id,
		"result": record.result,
		"reason": record.reason,
		"ip_address": record.ip_address,
		"user_agent": record.user_agent,
		"created_at": record.created_at,
	}


def _audit_log_from_document(document: dict) -> AuditLogRecord:
	return AuditLogRecord(
		audit_id=str(document["_id"]),
		organization_id=document["organization_id"],
		actor_user_id=document["actor_user_id"],
		action=document["action"],
		resource_type=document["resource_type"],
		resource_id=document.get("resource_id"),
		result=document["result"],
		reason=document.get("reason"),
		ip_address=document.get("ip_address"),
		user_agent=document.get("user_agent"),
		created_at=ensure_utc(document["created_at"]),
		floor_id=document.get("floor_id"),
	)


class AuditRepository:
	def __init__(self, client: MongoDatabaseClient) -> None:
		self._audit_logs = client.database[AUDIT_LOGS_COLLECTION]

	def append(self, record: AuditLogRecord) -> AuditLogRecord:
		self._audit_logs.insert_one(_audit_log_to_document(record))
		return record

	def list_logs(
		self,
		organization_id: str,
		*,
		actor_user_id: str | None = None,
		actor_user_ids: list[str] | None = None,
		floor_id: str | None = None,
		action: str | None = None,
		result: str | None = None,
		search: str | None = None,
	) -> list[AuditLogRecord]:
		query: dict = {"organization_id": organization_id}
		if actor_user_id is not None:
			query["actor_user_id"] = actor_user_id
		if actor_user_ids is not None:
			query["actor_user_id"] = {"$in": actor_user_ids}
		if floor_id is not None:
			query["floor_id"] = floor_id
		if action:
			query["action"] = action
		if result:
			query["result"] = result
		if search:
			pattern = re.compile(re.escape(search), re.IGNORECASE)
			query["$or"] = [
				{"action": pattern},
				{"resource_type": pattern},
				{"resource_id": pattern},
				{"reason": pattern},
				{"result": pattern},
			]
		return [_audit_log_from_document(d) for d in self._audit_logs.find(query).sort("created_at", DESCENDING)]
