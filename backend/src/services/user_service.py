from __future__ import annotations

from ..core.security.passwords import hash_password
from ..domain.entities.auth_session import AuthContext
from ..domain.enums.roles import Role
from ..domain.enums.statuses import Status
from ..domain.policies.access_policy import can_manage_users
from ..schemas.users import CreateUserRequest, UpdateUserRequest, UserItemResponse, UserListResponse
from ..utils.errors import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from ..utils.validation import normalize_email, validate_full_name, validate_registration_password


class UserService:
	def __init__(self, auth_repository, audit_service, settings) -> None:
		self._auth_repository = auth_repository
		self._audit_service = audit_service
		self._settings = settings

	def list_users(
		self,
		context: AuthContext,
		*,
		role: str | None = None,
		status: str | None = None,
		search: str | None = None,
		page: int,
		page_size: int,
	) -> UserListResponse:
		if not can_manage_users(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only admins can manage users.")
		users = self._auth_repository.list_users(
			context.user.organization_id,
			role=role,
			status=status,
			search=search,
		)
		total = len(users)
		start = (page - 1) * page_size
		items = [UserItemResponse.model_validate(u) for u in users[start:start + page_size]]
		return UserListResponse(items=items, page=page, page_size=page_size, total=total)

	def get_user(self, context: AuthContext, user_id: str) -> UserItemResponse:
		if not can_manage_users(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only admins can view user details.")
		user = self._auth_repository.get_user_by_id(user_id)
		if user is None or user.organization_id != context.user.organization_id:
			raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
		return UserItemResponse.model_validate(user)

	def create_user(
		self,
		context: AuthContext,
		payload: CreateUserRequest,
		*,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> UserItemResponse:
		if not can_manage_users(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only admins can create users.")
		email = normalize_email(payload.email)
		full_name = validate_full_name(payload.full_name)
		password = validate_registration_password(payload.password, self._settings.password_min_length)
		if payload.role not in {Role.ADMIN.value, Role.MANAGER.value, Role.USER.value}:
			raise ValidationAppError(code="invalid_role", message="role must be admin, manager, or user.")
		existing = self._auth_repository.get_user_by_email(context.user.organization_id, email)
		if existing is not None:
			raise ConflictError(code="email_already_exists", message="A user with this email already exists.")
		user = self._auth_repository.create_user(
			organization_id=context.user.organization_id,
			email=email,
			full_name=full_name,
			password_hash=hash_password(password),
			role=payload.role,
			status=Status.ACTIVE.value,
		)
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="create_user",
			resource_type="user",
			resource_id=user.user_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return UserItemResponse.model_validate(user)

	def update_user(
		self,
		context: AuthContext,
		user_id: str,
		payload: UpdateUserRequest,
		*,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> UserItemResponse:
		if not can_manage_users(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only admins can update users.")
		target = self._auth_repository.get_user_by_id(user_id)
		if target is None or target.organization_id != context.user.organization_id:
			raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
		if payload.role is not None and payload.role not in {Role.ADMIN.value, Role.MANAGER.value, Role.USER.value}:
			raise ValidationAppError(code="invalid_role", message="role must be admin, manager, or user.")
		if payload.status is not None and payload.status not in {Status.ACTIVE.value, Status.DISABLED.value, Status.PENDING.value}:
			raise ValidationAppError(code="invalid_status", message="status must be active, disabled, or pending.")
		updated = self._auth_repository.update_user(
			user_id,
			full_name=payload.full_name,
			role=payload.role,
			status=payload.status,
		)
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="update_user",
			resource_type="user",
			resource_id=user_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return UserItemResponse.model_validate(updated)

	def delete_user(
		self,
		context: AuthContext,
		user_id: str,
		*,
		ip_address: str | None = None,
		user_agent: str | None = None,
	):
		from ..schemas.auth import SuccessResponse
		if not can_manage_users(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only admins can delete users.")
		if user_id == context.user.user_id:
			raise ForbiddenError(code="forbidden", message="Admins cannot delete their own account.")
		target = self._auth_repository.get_user_by_id(user_id)
		if target is None or target.organization_id != context.user.organization_id:
			raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
		self._auth_repository.delete_user(user_id)
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="delete_user",
			resource_type="user",
			resource_id=user_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return SuccessResponse(success=True)
