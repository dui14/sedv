from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from ...api.dependencies.auth import get_auth_service, get_current_auth_context
from ...schemas.auth import AuthLoginRequest, AuthLogoutRequest, AuthRegisterRequest, AuthResponse, AuthUserResponse, SuccessResponse
from ...services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _request_metadata(request: Request) -> tuple[str | None, str | None]:
	client_host = request.client.host if request.client else None
	user_agent = request.headers.get("user-agent")
	return client_host, user_agent


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthRegisterRequest, request: Request, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.register(payload, ip_address=ip_address, user_agent=user_agent)


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthLoginRequest, request: Request, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.login(payload, ip_address=ip_address, user_agent=user_agent)


@router.get("/me", response_model=AuthUserResponse)
def me(current_context=Depends(get_current_auth_context), service: AuthService = Depends(get_auth_service)) -> AuthUserResponse:
	return service.me(current_context)


@router.post("/logout", response_model=SuccessResponse)
def logout(
	payload: AuthLogoutRequest,
	request: Request,
	current_context=Depends(get_current_auth_context),
	service: AuthService = Depends(get_auth_service),
) -> SuccessResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.logout(current_context, payload, ip_address=ip_address, user_agent=user_agent)