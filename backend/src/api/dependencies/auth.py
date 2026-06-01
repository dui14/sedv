from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...services.auth_service import AuthService
from ...utils.errors import UnauthorizedError


bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(request: Request) -> AuthService:
	return request.app.state.auth_service


def get_current_auth_context(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
	service: AuthService = Depends(get_auth_service),
):
	if credentials is None or credentials.scheme.lower() != "bearer":
		raise UnauthorizedError(code="unauthorized", message="Authentication is required.")
	return service.require_context(credentials.credentials)