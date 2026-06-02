from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status

from ...api.dependencies.auth import get_current_auth_context
from ...schemas.users import CreateUserRequest, UpdateUserRequest, UserItemResponse, UserListResponse
from ...schemas.auth import SuccessResponse

router = APIRouter(prefix="/users", tags=["users"])


def _get_user_service(request: Request):
	return request.app.state.user_service


def _request_meta(request: Request) -> tuple[str | None, str | None]:
	host = request.client.host if request.client else None
	ua = request.headers.get("user-agent")
	return host, ua


@router.get("", response_model=UserListResponse)
def list_users(
	request: Request,
	role: str | None = Query(default=None),
	status: str | None = Query(default=None),
	search: str | None = Query(default=None),
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_context=Depends(get_current_auth_context),
	service=Depends(_get_user_service),
) -> UserListResponse:
	return service.list_users(
		current_context,
		role=role,
		status=status,
		search=search,
		page=page,
		page_size=page_size,
	)


@router.get("/transfer-requests", response_model=UserListResponse)
def list_transfer_requests(
	request: Request,
	current_context=Depends(get_current_auth_context),
	service=Depends(_get_user_service),
) -> UserListResponse:
	return service.list_transfer_requests(current_context)


@router.post("", response_model=UserItemResponse, status_code=status.HTTP_201_CREATED)
def create_user(
	request: Request,
	payload: CreateUserRequest,
	current_context=Depends(get_current_auth_context),
	service=Depends(_get_user_service),
) -> UserItemResponse:
	ip, ua = _request_meta(request)
	return service.create_user(current_context, payload, ip_address=ip, user_agent=ua)


@router.get("/{user_id}", response_model=UserItemResponse)
def get_user(
	user_id: str,
	current_context=Depends(get_current_auth_context),
	service=Depends(_get_user_service),
) -> UserItemResponse:
	return service.get_user(current_context, user_id)


@router.patch("/{user_id}", response_model=UserItemResponse)
def update_user(
	user_id: str,
	request: Request,
	payload: UpdateUserRequest,
	current_context=Depends(get_current_auth_context),
	service=Depends(_get_user_service),
) -> UserItemResponse:
	ip, ua = _request_meta(request)
	return service.update_user(current_context, user_id, payload, ip_address=ip, user_agent=ua)


@router.post("/{user_id}/approve-transfer", response_model=UserItemResponse)
def approve_transfer(
	user_id: str,
	request: Request,
	current_context=Depends(get_current_auth_context),
	service=Depends(_get_user_service),
) -> UserItemResponse:
	ip, ua = _request_meta(request)
	return service.approve_transfer(current_context, user_id, ip_address=ip, user_agent=ua)


@router.post("/{user_id}/reject-transfer", response_model=UserItemResponse)
def reject_transfer(
	user_id: str,
	request: Request,
	current_context=Depends(get_current_auth_context),
	service=Depends(_get_user_service),
) -> UserItemResponse:
	ip, ua = _request_meta(request)
	return service.reject_transfer(current_context, user_id, ip_address=ip, user_agent=ua)


@router.delete("/{user_id}", response_model=SuccessResponse)
def delete_user(
	user_id: str,
	request: Request,
	current_context=Depends(get_current_auth_context),
	service=Depends(_get_user_service),
) -> SuccessResponse:
	ip, ua = _request_meta(request)
	return service.delete_user(current_context, user_id, ip_address=ip, user_agent=ua)
