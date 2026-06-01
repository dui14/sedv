from __future__ import annotations

from ..enums.roles import Role
from ..enums.statuses import PublishStatus, Status, VaultType


def is_active(status: str) -> bool:
	return status == Status.ACTIVE.value


def can_access_auth_context(role: str) -> bool:
	return role in {Role.ADMIN.value, Role.MANAGER.value, Role.USER.value}


def can_view_all_files(role: str) -> bool:
	return role in {Role.ADMIN.value, Role.MANAGER.value}


def can_manage_all_files(role: str) -> bool:
	return role in {Role.ADMIN.value, Role.MANAGER.value}


def can_view_file(role: str, *, actor_user_id: str, owner_user_id: str, vault_type: str, publish_status: str) -> bool:
	if vault_type == VaultType.PRIVATE.value:
		return role == Role.ADMIN.value or actor_user_id == owner_user_id
	if vault_type == VaultType.GENERAL.value:
		if publish_status == PublishStatus.PUBLISHED.value:
			return True
		return role in {Role.ADMIN.value, Role.MANAGER.value} or actor_user_id == owner_user_id
	return can_view_all_files(role) or actor_user_id == owner_user_id


def can_download_file(role: str, *, actor_user_id: str, owner_user_id: str, vault_type: str, publish_status: str) -> bool:
	return can_view_file(role, actor_user_id=actor_user_id, owner_user_id=owner_user_id, vault_type=vault_type, publish_status=publish_status)


def can_delete_file(role: str, *, actor_user_id: str, owner_user_id: str) -> bool:
	return can_manage_all_files(role) or actor_user_id == owner_user_id


def can_approve_file(role: str) -> bool:
	return role in {Role.ADMIN.value, Role.MANAGER.value}


def can_manage_users(role: str) -> bool:
	return role == Role.ADMIN.value


def can_view_all_audit_logs(role: str) -> bool:
	return role == Role.ADMIN.value


def can_view_general_audit_logs(role: str) -> bool:
	return role in {Role.ADMIN.value, Role.MANAGER.value}


def can_view_audit_log(role: str, *, actor_user_id: str, log_actor_user_id: str, vault_type: str | None = None) -> bool:
	if role == Role.ADMIN.value:
		return True
	if role == Role.MANAGER.value:
		return vault_type == VaultType.GENERAL.value or vault_type is None
	return actor_user_id == log_actor_user_id