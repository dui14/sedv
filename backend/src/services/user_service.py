from __future__ import annotations

from ..core.security.passwords import hash_password
from ..domain.entities.auth_session import AuthContext
from ..domain.enums.roles import Role
from ..domain.enums.statuses import Status
from ..domain.policies.access_policy import can_manage_any_user, can_manage_users
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
			raise ForbiddenError(code="forbidden", message="Access denied.")
		floor_id = None if can_manage_any_user(context.user.role) else context.user.floor_id
		users = self._auth_repository.list_users(
			context.user.organization_id,
			role=role,
			status=status,
			search=search,
			floor_id=floor_id,
		)
		total = len(users)
		start = (page - 1) * page_size
		items = [UserItemResponse.model_validate(u) for u in users[start:start + page_size]]
		return UserListResponse(items=items, page=page, page_size=page_size, total=total)

	def list_transfer_requests(self, context: AuthContext) -> UserListResponse:
		if context.user.role not in {Role.ADMIN.value, Role.COMPANY.value}:
			raise ForbiddenError(code="forbidden", message="Access denied.")
		if can_manage_any_user(context.user.role):
			users = []
			floors = self._auth_repository.list_floors(context.user.organization_id)
			for floor in floors:
				users.extend(self._auth_repository.list_pending_transfers(context.user.organization_id, floor.floor_id))
		else:
			users = self._auth_repository.list_pending_transfers(
				context.user.organization_id, context.user.floor_id
			)
		return UserListResponse(items=[UserItemResponse.model_validate(u) for u in users], page=1, page_size=len(users), total=len(users))

	def approve_transfer(
		self,
		context: AuthContext,
		user_id: str,
		*,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> UserItemResponse:
		if context.user.role not in {Role.ADMIN.value, Role.COMPANY.value}:
			raise ForbiddenError(code="forbidden", message="Access denied.")
		target = self._auth_repository.get_user_by_id(user_id)
		if target is None or target.organization_id != context.user.organization_id:
			raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
		if not can_manage_any_user(context.user.role):
			if target.pending_floor_id != context.user.floor_id:
				raise ForbiddenError(code="forbidden", message="This transfer request is not for your floor.")
		updated = self._auth_repository.approve_floor_transfer(user_id)
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="approve_transfer",
			resource_type="user",
			resource_id=user_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return UserItemResponse.model_validate(updated)

	def reject_transfer(
		self,
		context: AuthContext,
		user_id: str,
		*,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> UserItemResponse:
		if context.user.role not in {Role.ADMIN.value, Role.COMPANY.value}:
			raise ForbiddenError(code="forbidden", message="Access denied.")
		target = self._auth_repository.get_user_by_id(user_id)
		if target is None or target.organization_id != context.user.organization_id:
			raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
		if not can_manage_any_user(context.user.role):
			if target.pending_floor_id != context.user.floor_id:
				raise ForbiddenError(code="forbidden", message="This transfer request is not for your floor.")
		updated = self._auth_repository.reject_floor_transfer(user_id)
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="reject_transfer",
			resource_type="user",
			resource_id=user_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return UserItemResponse.model_validate(updated)

	def get_user(self, context: AuthContext, user_id: str) -> UserItemResponse:
		if not can_manage_users(context.user.role):
			raise ForbiddenError(code="forbidden", message="Access denied.")
		user = self._auth_repository.get_user_by_id(user_id)
		if user is None or user.organization_id != context.user.organization_id:
			raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
		if not can_manage_any_user(context.user.role):
			if user.floor_id != context.user.floor_id:
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
			raise ForbiddenError(code="forbidden", message="Access denied.")
		email = normalize_email(payload.email)
		full_name = validate_full_name(payload.full_name)
		password = validate_registration_password(payload.password, self._settings.password_min_length)

		if can_manage_any_user(context.user.role):
			allowed_roles = {Role.COMPANY.value, Role.ADMIN.value, Role.MANAGER.value, Role.USER.value}
			floor_id = payload.floor_id
		else:
			allowed_roles = {Role.MANAGER.value, Role.USER.value}
			floor_id = context.user.floor_id

		if payload.role not in allowed_roles:
			raise ValidationAppError(code="invalid_role", message=f"Role must be one of: {', '.join(sorted(allowed_roles))}.")

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
			floor_id=floor_id,
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
			raise ForbiddenError(code="forbidden", message="Access denied.")
		target = self._auth_repository.get_user_by_id(user_id)
		if target is None or target.organization_id != context.user.organization_id:
			raise NotFoundError(code="user_not_found", message="The requested user could not be found.")

		if not can_manage_any_user(context.user.role):
			if target.floor_id != context.user.floor_id:
				raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
			if target.role == Role.ADMIN.value:
				raise ForbiddenError(code="forbidden", message="Admin accounts cannot be edited here.")
			if target.role == Role.COMPANY.value:
				raise ForbiddenError(code="forbidden", message="Company accounts cannot be edited here.")
			if payload.role is not None and payload.role not in {Role.MANAGER.value, Role.USER.value}:
				raise ValidationAppError(code="invalid_role", message="role must be manager or user.")
		else:
			if target.user_id == context.user.user_id:
				raise ForbiddenError(code="forbidden", message="Cannot edit your own account here.")

		if payload.status is not None and payload.status not in {Status.ACTIVE.value, Status.DISABLED.value, Status.PENDING.value}:
			raise ValidationAppError(code="invalid_status", message="status must be active, disabled, or pending.")

		if payload.floor_id is not None and payload.floor_id != target.floor_id:
			updated = self._auth_repository.initiate_floor_transfer(user_id, payload.floor_id)
			self._audit_service.record_event(
				organization_id=context.user.organization_id,
				actor_user_id=context.user.user_id,
				action="initiate_transfer",
				resource_type="user",
				resource_id=user_id,
				result="success",
				reason=f"pending_floor_id={payload.floor_id}",
				ip_address=ip_address,
				user_agent=user_agent,
			)
			return UserItemResponse.model_validate(updated)

		email = normalize_email(payload.email) if payload.email is not None else None
		full_name = validate_full_name(payload.full_name) if payload.full_name is not None else None
		password_hash = None
		if payload.password is not None:
			password = validate_registration_password(payload.password, self._settings.password_min_length)
			password_hash = hash_password(password)
		if email is not None and email != target.email:
			existing = self._auth_repository.get_user_by_email(context.user.organization_id, email)
			if existing is not None and existing.user_id != user_id:
				raise ConflictError(code="email_already_exists", message="A user with this email already exists.")
		updated = self._auth_repository.update_user(
			user_id,
			email=email,
			full_name=full_name,
			password_hash=password_hash,
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
			raise ForbiddenError(code="forbidden", message="Access denied.")
		if user_id == context.user.user_id:
			raise ForbiddenError(code="forbidden", message="Cannot delete your own account.")
		target = self._auth_repository.get_user_by_id(user_id)
		if target is None or target.organization_id != context.user.organization_id:
			raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
		if not can_manage_any_user(context.user.role):
			if target.floor_id != context.user.floor_id:
				raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
			if target.role in {Role.ADMIN.value, Role.COMPANY.value}:
				raise ForbiddenError(code="forbidden", message="Cannot delete this account.")
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
