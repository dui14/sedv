from __future__ import annotations

from ..enums.roles import Role
from ..enums.statuses import PublishStatus, Status, VaultType


def is_active(status: str) -> bool:
	return status == Status.ACTIVE.value


def can_access_auth_context(role: str) -> bool:
	return role in {Role.COMPANY.value, Role.ADMIN.value, Role.MANAGER.value, Role.USER.value}


def can_view_all_files(role: str) -> bool:
	return role in {Role.COMPANY.value, Role.ADMIN.value, Role.MANAGER.value}


def can_manage_all_files(role: str) -> bool:
	return role in {Role.COMPANY.value, Role.ADMIN.value, Role.MANAGER.value}


def can_view_file(
	role: str,
	*,
	actor_user_id: str,
	actor_floor_id: str | None,
	owner_user_id: str,
	file_floor_id: str | None,
	vault_type: str,
	publish_status: str,
) -> bool:
	if vault_type == VaultType.PRIVATE.value:
		if role == Role.COMPANY.value:
			return True
		if role == Role.ADMIN.value:
			return actor_floor_id is not None and actor_floor_id == file_floor_id
		return actor_user_id == owner_user_id

	if vault_type == VaultType.FLOOR.value:
		if publish_status == PublishStatus.PUBLISHED.value:
			if role == Role.COMPANY.value:
				return True
			return actor_floor_id is not None and actor_floor_id == file_floor_id
		if role in {Role.COMPANY.value, Role.ADMIN.value, Role.MANAGER.value}:
			return True
		return actor_user_id == owner_user_id

	if vault_type == VaultType.COMPANY.value:
		if publish_status == PublishStatus.PUBLISHED.value:
			return True
		if role in {Role.COMPANY.value, Role.ADMIN.value, Role.MANAGER.value}:
			return True
		return actor_user_id == owner_user_id

	return can_view_all_files(role) or actor_user_id == owner_user_id


def can_download_file(
	role: str,
	*,
	actor_user_id: str,
	actor_floor_id: str | None,
	owner_user_id: str,
	file_floor_id: str | None,
	vault_type: str,
	publish_status: str,
) -> bool:
	return can_view_file(
		role,
		actor_user_id=actor_user_id,
		actor_floor_id=actor_floor_id,
		owner_user_id=owner_user_id,
		file_floor_id=file_floor_id,
		vault_type=vault_type,
		publish_status=publish_status,
	)


def can_delete_file(role: str, *, actor_user_id: str, owner_user_id: str) -> bool:
	return can_manage_all_files(role) or actor_user_id == owner_user_id


def can_approve_file(role: str) -> bool:
	return role in {Role.COMPANY.value, Role.ADMIN.value, Role.MANAGER.value}


def can_approve_target(role: str, target: str) -> bool:
	if target == "floor":
		return role == Role.MANAGER.value
	if target == "company":
		return role in {Role.ADMIN.value, Role.COMPANY.value}
	return False


def can_manage_users(role: str) -> bool:
	return role in {Role.COMPANY.value, Role.ADMIN.value}


def can_manage_any_user(role: str) -> bool:
	return role == Role.COMPANY.value


def can_view_all_audit_logs(role: str) -> bool:
	return role == Role.COMPANY.value


def can_view_floor_audit_logs(role: str) -> bool:
	return role in {Role.COMPANY.value, Role.ADMIN.value}
