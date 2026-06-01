from __future__ import annotations

from dataclasses import dataclass

from ..core.config.settings import Settings
from ..core.security.jwt import AccessTokenClaims, decode_access_token, encode_access_token
from ..core.security.passwords import hash_password, verify_password
from ..domain.entities.auth_session import AuthContext
from ..domain.enums.statuses import Status
from ..schemas.auth import AuthLoginRequest, AuthLogoutRequest, AuthRegisterRequest, AuthResponse, AuthUserResponse, SuccessResponse
from ..utils.datetime import now_utc
from ..utils.errors import ConflictError, ForbiddenError, UnauthorizedError, ValidationAppError
from ..utils.ids import new_jti
from ..utils.validation import normalize_email, validate_full_name, validate_login_password, validate_registration_password, validate_reason


@dataclass(slots=True)
class AuthServiceDependencies:
	repository: object
	audit_service: object
	settings: Settings


class AuthService:
	def __init__(self, repository, audit_service, settings: Settings) -> None:
		self._repository = repository
		self._audit_service = audit_service
		self._settings = settings

	def register(self, payload: AuthRegisterRequest, *, ip_address: str | None = None, user_agent: str | None = None) -> AuthResponse:
		email = normalize_email(payload.email)
		password = validate_registration_password(payload.password, self._settings.password_min_length)
		full_name = validate_full_name(payload.full_name)
		organization = self._repository.get_demo_organization()

		existing = self._repository.get_user_by_email(organization.organization_id, email)
		if existing is not None:
			self._audit_service.record_event(
				organization_id=organization.organization_id,
				actor_user_id=existing.user_id,
				action="register",
				resource_type="user",
				resource_id=existing.user_id,
				result="denied",
				reason="email_already_exists",
				ip_address=ip_address,
				user_agent=user_agent,
			)
			raise ConflictError(code="email_already_exists", message="A user with this email already exists.")

		user = self._repository.create_user(
			organization_id=organization.organization_id,
			email=email,
			full_name=full_name,
			password_hash=hash_password(password),
			role="user",
			status=Status.ACTIVE.value,
		)
		return self._issue_auth_response(
			user.user_id,
			action="register",
			actor_user_id=user.user_id,
			organization_id=organization.organization_id,
			ip_address=ip_address,
			user_agent=user_agent,
		)

	def login(self, payload: AuthLoginRequest, *, ip_address: str | None = None, user_agent: str | None = None) -> AuthResponse:
		email = normalize_email(payload.email)
		password = validate_login_password(payload.password)
		organization = self._repository.get_demo_organization()
		user = self._repository.get_user_by_email(organization.organization_id, email)

		if user is None or user.password_hash is None or not verify_password(password, user.password_hash):
			self._audit_service.record_event(
				organization_id=organization.organization_id,
				actor_user_id=user.user_id if user is not None else "anonymous",
				action="login",
				resource_type="auth_session",
				result="denied",
				reason="invalid_credentials",
				ip_address=ip_address,
				user_agent=user_agent,
			)
			raise UnauthorizedError(code="invalid_credentials", message="The email or password is incorrect.")

		if user.status != Status.ACTIVE.value:
			self._audit_service.record_event(
				organization_id=organization.organization_id,
				actor_user_id=user.user_id,
				action="login",
				resource_type="auth_session",
				result="denied",
				reason="account_disabled",
				ip_address=ip_address,
				user_agent=user_agent,
			)
			raise ForbiddenError(code="account_disabled", message="This account is disabled.")

		return self._issue_auth_response(
			user.user_id,
			action="login",
			actor_user_id=user.user_id,
			organization_id=organization.organization_id,
			ip_address=ip_address,
			user_agent=user_agent,
			update_identity=False,
		)

	def require_context(self, token: str) -> AuthContext:
		claims = decode_access_token(token, self._settings.jwt_secret)
		session = self._repository.get_session_by_jti(claims.jti)
		if session is None or session.revoked_at is not None:
			raise UnauthorizedError(code="unauthorized", message="The access token is invalid or expired.")
		now = now_utc()
		if session.expires_at <= now or claims.exp <= int(now.timestamp()):
			raise UnauthorizedError(code="unauthorized", message="The access token is invalid or expired.")
		user = self._repository.get_user_by_id(claims.sub)
		if user is None:
			raise UnauthorizedError(code="unauthorized", message="The access token is invalid or expired.")
		if user.status != Status.ACTIVE.value:
			raise ForbiddenError(code="account_disabled", message="This account is disabled.")
		return AuthContext(token=token, claims_jti=claims.jti, session=session, user=user)

	def me(self, context: AuthContext) -> AuthUserResponse:
		if context.user.status != Status.ACTIVE.value:
			raise ForbiddenError(code="account_disabled", message="This account is disabled.")
		return AuthUserResponse.model_validate(context.user)

	def logout(self, context: AuthContext, payload: AuthLogoutRequest, *, ip_address: str | None = None, user_agent: str | None = None) -> SuccessResponse:
		reason = validate_reason(payload.reason)
		self._repository.revoke_session(context.claims_jti, now_utc())
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="logout",
			resource_type="auth_session",
			resource_id=context.session.session_id,
			result="success",
			reason=reason,
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return SuccessResponse(success=True)

	def _issue_auth_response(
		self,
		user_id: str,
		*,
		action: str,
		actor_user_id: str,
		organization_id: str,
		ip_address: str | None,
		user_agent: str | None,
		update_identity: bool = True,
	) -> AuthResponse:
		user = self._repository.get_user_by_id(user_id)
		if user is None:
			raise UnauthorizedError(code="unauthorized", message="The access token is invalid or expired.")
		if user.status != Status.ACTIVE.value:
			raise ForbiddenError(code="account_disabled", message="This account is disabled.")

		now = now_utc()
		jti = new_jti()
		expires_at = now.replace(microsecond=0) + self._settings_token_delta()
		session = self._repository.create_session(
			organization_id=organization_id,
			user_id=user.user_id,
			jti=jti,
			issued_at=now,
			expires_at=expires_at,
		)
		updated_user = self._repository.update_last_login(user.user_id, now)
		claims = AccessTokenClaims(
			sub=updated_user.user_id,
			org=updated_user.organization_id,
			jti=session.jti,
			email=updated_user.email,
			full_name=updated_user.full_name,
			role=updated_user.role,
			status=updated_user.status,
			iat=int(now.timestamp()),
			exp=int(expires_at.timestamp()),
		)
		token = encode_access_token(claims, self._settings.jwt_secret)
		self._audit_service.record_event(
			organization_id=organization_id,
			actor_user_id=actor_user_id,
			action=action,
			resource_type="auth_session",
			resource_id=session.session_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return AuthResponse(user=AuthUserResponse.model_validate(updated_user), access_token=token)

	def _settings_token_delta(self):
		from datetime import timedelta

		return timedelta(seconds=self._settings.token_ttl_seconds)