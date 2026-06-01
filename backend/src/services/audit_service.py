from __future__ import annotations

from datetime import datetime

from ..domain.entities.audit_log import AuditLogRecord
from ..domain.entities.auth_session import AuthContext
from ..domain.enums.roles import Role
from ..schemas.audit import AuditLogItemResponse, AuditLogListResponse
from ..utils.datetime import now_utc
from ..utils.ids import new_id
from ..utils.validation import validate_search_term


class AuditService:
	def __init__(self, repository, auth_repository=None) -> None:
		self._repository = repository
		self._auth_repository = auth_repository

	def record_event(
		self,
		*,
		organization_id: str,
		actor_user_id: str,
		action: str,
		resource_type: str,
		result: str,
		resource_id: str | None = None,
		reason: str | None = None,
		ip_address: str | None = None,
		user_agent: str | None = None,
		created_at: datetime | None = None,
	) -> AuditLogRecord:
		record = AuditLogRecord(
			audit_id=new_id(),
			organization_id=organization_id,
			actor_user_id=actor_user_id,
			action=action,
			resource_type=resource_type,
			resource_id=resource_id,
			result=result,
			reason=reason,
			ip_address=ip_address,
			user_agent=user_agent,
			created_at=created_at or now_utc(),
		)
		return self._repository.append(record)

	def list_logs(
		self,
		context: AuthContext,
		*,
		action: str | None,
		result: str | None,
		search: str | None,
		page: int,
		page_size: int,
		actor_filter: str | None = None,
	) -> AuditLogListResponse:
		term = validate_search_term(search)
		role = context.user.role

		scoped_actor_user_id: str | None = None
		general_only = False

		if role == Role.ADMIN.value:
			scoped_actor_user_id = actor_filter
		elif role == Role.MANAGER.value:
			general_only = True
			scoped_actor_user_id = actor_filter
		else:
			scoped_actor_user_id = context.user.user_id

		records = self._repository.list_logs(
			context.user.organization_id,
			actor_user_id=scoped_actor_user_id,
			action=action.strip() if action else None,
			result=result.strip() if result else None,
			search=term,
			general_only=general_only,
		)
		total = len(records)
		start = (page - 1) * page_size
		end = start + page_size
		return AuditLogListResponse(
			items=[self._to_item_response(record) for record in records[start:end]],
			page=page,
			page_size=page_size,
			total=total,
		)

	def my_activity(
		self,
		context: AuthContext,
		*,
		page: int,
		page_size: int,
	) -> AuditLogListResponse:
		records = self._repository.list_logs(
			context.user.organization_id,
			actor_user_id=context.user.user_id,
		)
		total = len(records)
		start = (page - 1) * page_size
		end = start + page_size
		return AuditLogListResponse(
			items=[self._to_item_response(record) for record in records[start:end]],
			page=page,
			page_size=page_size,
			total=total,
		)

	def _to_item_response(self, record: AuditLogRecord) -> AuditLogItemResponse:
		actor = self._auth_repository.get_user_by_id(record.actor_user_id) if self._auth_repository is not None else None
		return AuditLogItemResponse(
			audit_id=record.audit_id,
			organization_id=record.organization_id,
			actor_user_id=record.actor_user_id,
			actor_name=actor.full_name if actor is not None else record.actor_user_id,
			action=record.action,
			resource_type=record.resource_type,
			resource_id=record.resource_id,
			result=record.result,
			reason=record.reason,
			created_at=record.created_at,
		)
