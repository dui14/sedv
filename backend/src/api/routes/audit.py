from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ...api.dependencies.auth import get_current_auth_context
from ...schemas.audit import AuditLogListResponse

router = APIRouter(prefix="/audit-logs", tags=["audit"])


def get_audit_service(request: Request):
	return request.app.state.audit_service


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
	action: str | None = Query(default=None),
	result: str | None = Query(default=None),
	search: str | None = Query(default=None),
	actor: str | None = Query(default=None),
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=50, ge=1, le=100),
	current_context=Depends(get_current_auth_context),
	service=Depends(get_audit_service),
) -> AuditLogListResponse:
	return service.list_logs(
		current_context,
		action=action,
		result=result,
		search=search,
		page=page,
		page_size=page_size,
		actor_filter=actor,
	)


@router.get("/my-activity", response_model=AuditLogListResponse)
def my_activity(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=50, ge=1, le=100),
	current_context=Depends(get_current_auth_context),
	service=Depends(get_audit_service),
) -> AuditLogListResponse:
	return service.my_activity(current_context, page=page, page_size=page_size)
