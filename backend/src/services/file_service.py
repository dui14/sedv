from __future__ import annotations

from dataclasses import dataclass

from cryptography.exceptions import InvalidTag

from ..core.config.settings import Settings
from ..domain.entities.auth_session import AuthContext
from ..domain.entities.file import FileRecord
from ..domain.enums.statuses import PublishStatus, RequestStatus, Status, VaultType
from ..domain.policies.access_policy import (
	can_approve_file,
	can_delete_file,
	can_download_file,
	can_manage_users,
	can_view_all_files,
	can_view_file,
)
from ..infrastructure.crypto.encryption import decrypt_bytes, derive_file_key, encrypt_bytes
from ..infrastructure.crypto.hashing import sha256_hex
from ..infrastructure.filesystem.storage import EncryptedBlobStorage
from ..schemas.files import (
	FileAdminUpdateRequest,
	FileDeleteResponse,
	FileItemResponse,
	FileListResponse,
	PublishRequestListResponse,
	PublishRequestResponse,
)
from ..utils.datetime import now_utc
from ..utils.errors import AppError, ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from ..utils.ids import new_id
from ..utils.validation import validate_file_name, validate_search_term, validate_upload_bytes, validate_upload_mime_type


@dataclass(slots=True)
class FileDownloadResult:
	record: FileRecord
	content: bytes


class FileService:
	def __init__(self, file_repository, auth_repository, audit_service, settings: Settings) -> None:
		self._file_repository = file_repository
		self._auth_repository = auth_repository
		self._audit_service = audit_service
		self._settings = settings
		self._storage = EncryptedBlobStorage(settings.file_storage_root)
		self._file_key = derive_file_key(settings.file_encryption_key_seed)

	def list_files(
		self,
		context: AuthContext,
		*,
		search: str | None,
		page: int,
		page_size: int,
		vault_type: str | None = None,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> FileListResponse:
		term = validate_search_term(search)
		role = context.user.role

		if role == "admin":
			records = self._file_repository.list_files(
				context.user.organization_id,
				vault_type=vault_type,
				search=term,
			)
		elif role == "manager":
			records = self._file_repository.list_files(
				context.user.organization_id,
				vault_type="general" if vault_type is None else vault_type,
				search=term,
			)
		else:
			if vault_type == "private":
				records = self._file_repository.list_files(
					context.user.organization_id,
					owner_user_id=context.user.user_id,
					vault_type="private",
					search=term,
				)
			elif vault_type == "general":
				all_general = self._file_repository.list_files(
					context.user.organization_id,
					vault_type="general",
					search=term,
				)
				records = [
					r for r in all_general
					if r.publish_status == PublishStatus.PUBLISHED.value or r.owner_user_id == context.user.user_id
				]
			else:
				private_records = self._file_repository.list_files(
					context.user.organization_id,
					owner_user_id=context.user.user_id,
					vault_type="private",
					search=term,
				)
				general_published = [
					r for r in self._file_repository.list_files(
						context.user.organization_id,
						vault_type="general",
						search=term,
					)
					if r.publish_status == PublishStatus.PUBLISHED.value or r.owner_user_id == context.user.user_id
				]
				records = private_records + general_published

		total = len(records)
		start = (page - 1) * page_size
		end = start + page_size
		items = [self._to_item_response(record) for record in records[start:end]]
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="search",
			resource_type="file",
			result="success",
			reason=term,
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return FileListResponse(items=items, page=page, page_size=page_size, total=total)

	def upload_file(
		self,
		context: AuthContext,
		*,
		filename: str | None,
		content_type: str | None,
		content: bytes,
		vault_type: str = "general",
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> FileItemResponse:
		storage_name = None
		try:
			if vault_type not in {VaultType.GENERAL.value, VaultType.PRIVATE.value}:
				raise ValidationAppError(code="invalid_vault_type", message="vault_type must be general or private.")
			original_name = validate_file_name(filename)
			mime_type = validate_upload_mime_type(content_type, self._settings.allowed_upload_mime_types)
			payload = validate_upload_bytes(content, self._settings.max_upload_size_bytes)
			plain_sha256 = sha256_hex(payload)
			encrypted_bytes, encryption_iv = encrypt_bytes(payload, self._file_key)
			storage_name = f"{new_id()}.bin"
			storage_path = self._storage.write(storage_name, encrypted_bytes)
			now = now_utc()

			if vault_type == VaultType.GENERAL.value:
				publish_status = PublishStatus.PENDING.value
			else:
				publish_status = PublishStatus.NOT_APPLICABLE.value

			record = FileRecord(
				file_id=new_id(),
				organization_id=context.user.organization_id,
				owner_user_id=context.user.user_id,
				uploaded_by_user_id=context.user.user_id,
				original_name=original_name,
				storage_name=storage_name,
				storage_path=storage_path,
				mime_type=mime_type,
				size_bytes=len(payload),
				sha256=plain_sha256,
				encryption_algorithm="AES-256-GCM",
				encryption_iv=encryption_iv,
				encryption_key_version=self._settings.file_encryption_key_version,
				vault_type=vault_type,
				publish_status=publish_status,
				reviewed_by_user_id=None,
				reviewed_at=None,
				review_note=None,
				status=Status.ACTIVE.value,
				deleted_at=None,
				created_at=now,
				updated_at=now,
			)
			created = self._file_repository.create_file(record)
			self._audit_service.record_event(
				organization_id=context.user.organization_id,
				actor_user_id=context.user.user_id,
				action="upload",
				resource_type="file",
				resource_id=created.file_id,
				result="success",
				reason=f"vault_type={vault_type}",
				ip_address=ip_address,
				user_agent=user_agent,
			)
			return self._to_item_response(created)
		except Exception as exc:
			if storage_name is not None:
				try:
					self._storage.delete(storage_name)
				except FileNotFoundError:
					pass
			if isinstance(exc, AppError):
				self._audit_service.record_event(
					organization_id=context.user.organization_id,
					actor_user_id=context.user.user_id,
					action="upload",
					resource_type="file",
					result="error",
					reason=exc.code,
					ip_address=ip_address,
					user_agent=user_agent,
				)
			raise

	def get_file(self, context: AuthContext, file_id: str, *, ip_address: str | None = None, user_agent: str | None = None) -> FileItemResponse:
		record = self._resolve_visible_file(context, file_id)
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="search",
			resource_type="file",
			resource_id=record.file_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return self._to_item_response(record)

	def download_file(self, context: AuthContext, file_id: str, *, ip_address: str | None = None, user_agent: str | None = None) -> FileDownloadResult:
		record = self._resolve_visible_file(context, file_id)
		if not can_download_file(
			context.user.role,
			actor_user_id=context.user.user_id,
			owner_user_id=record.owner_user_id,
			vault_type=record.vault_type,
			publish_status=record.publish_status,
		):
			self._audit_service.record_event(
				organization_id=context.user.organization_id,
				actor_user_id=context.user.user_id,
				action="denied_access",
				resource_type="file",
				resource_id=record.file_id,
				result="denied",
				reason="download_forbidden",
			)
			raise ForbiddenError(code="forbidden", message="You do not have permission to download this file.")
		try:
			encrypted_bytes = self._storage.read(record.storage_name)
			plaintext = decrypt_bytes(encrypted_bytes, self._file_key, record.encryption_iv)
		except (FileNotFoundError, InvalidTag, ValueError) as exc:
			self._audit_service.record_event(
				organization_id=context.user.organization_id,
				actor_user_id=context.user.user_id,
				action="download",
				resource_type="file",
				resource_id=record.file_id,
				result="error",
				reason="integrity_check_failed",
				ip_address=ip_address,
				user_agent=user_agent,
			)
			raise ConflictError(code="integrity_check_failed", message="The file integrity check failed.") from exc
		if sha256_hex(plaintext) != record.sha256:
			self._audit_service.record_event(
				organization_id=context.user.organization_id,
				actor_user_id=context.user.user_id,
				action="download",
				resource_type="file",
				resource_id=record.file_id,
				result="error",
				reason="integrity_check_failed",
				ip_address=ip_address,
				user_agent=user_agent,
			)
			raise ConflictError(code="integrity_check_failed", message="The file integrity check failed.")
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="download",
			resource_type="file",
			resource_id=record.file_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return FileDownloadResult(record=record, content=plaintext)

	def delete_file(self, context: AuthContext, file_id: str, *, ip_address: str | None = None, user_agent: str | None = None) -> FileDeleteResponse:
		record = self._resolve_visible_file(context, file_id, for_delete=True)
		try:
			self._storage.delete(record.storage_name)
		except OSError as exc:
			self._audit_service.record_event(
				organization_id=context.user.organization_id,
				actor_user_id=context.user.user_id,
				action="delete",
				resource_type="file",
				resource_id=record.file_id,
				result="error",
				reason="file_not_found",
				ip_address=ip_address,
				user_agent=user_agent,
			)
			raise NotFoundError(code="file_not_found", message="The requested file could not be found.") from exc
		self._file_repository.mark_deleted(record.file_id, now_utc())
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="delete",
			resource_type="file",
			resource_id=record.file_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return FileDeleteResponse(success=True, deleted_file_id=record.file_id)

	def approve_file(
		self,
		context: AuthContext,
		file_id: str,
		*,
		note: str | None = None,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> FileItemResponse:
		if not can_approve_file(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only managers and admins can approve files.")
		record = self._file_repository.get_file_by_id(file_id)
		if record is None or record.organization_id != context.user.organization_id or record.status != Status.ACTIVE.value:
			raise NotFoundError(code="file_not_found", message="The requested file could not be found.")
		if record.vault_type != VaultType.GENERAL.value:
			raise ForbiddenError(code="forbidden", message="Only general vault files can be approved.")
		if record.publish_status != PublishStatus.PENDING.value:
			raise ConflictError(code="not_pending", message="File is not in pending state.")
		now = now_utc()
		updated = self._file_repository.update_publish_status(
			file_id,
			publish_status=PublishStatus.PUBLISHED.value,
			reviewed_by_user_id=context.user.user_id,
			reviewed_at=now,
			review_note=note,
		)
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="approve",
			resource_type="file",
			resource_id=file_id,
			result="success",
			reason=note,
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return self._to_item_response(updated)

	def reject_file(
		self,
		context: AuthContext,
		file_id: str,
		*,
		note: str | None = None,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> FileItemResponse:
		if not can_approve_file(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only managers and admins can reject files.")
		record = self._file_repository.get_file_by_id(file_id)
		if record is None or record.organization_id != context.user.organization_id or record.status != Status.ACTIVE.value:
			raise NotFoundError(code="file_not_found", message="The requested file could not be found.")
		if record.vault_type != VaultType.GENERAL.value:
			raise ForbiddenError(code="forbidden", message="Only general vault files can be rejected.")
		if record.publish_status != PublishStatus.PENDING.value:
			raise ConflictError(code="not_pending", message="File is not in pending state.")
		now = now_utc()
		updated = self._file_repository.update_publish_status(
			file_id,
			publish_status=PublishStatus.REJECTED.value,
			reviewed_by_user_id=context.user.user_id,
			reviewed_at=now,
			review_note=note,
		)
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="reject",
			resource_type="file",
			resource_id=file_id,
			result="success",
			reason=note,
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return self._to_item_response(updated)

	def list_pending_approvals(
		self,
		context: AuthContext,
		*,
		page: int,
		page_size: int,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> FileListResponse:
		if not can_approve_file(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only managers and admins can view the approval queue.")
		records = self._file_repository.list_files(
			context.user.organization_id,
			vault_type=VaultType.GENERAL.value,
			publish_status=PublishStatus.PENDING.value,
		)
		total = len(records)
		start = (page - 1) * page_size
		items = [self._to_item_response(r) for r in records[start:start + page_size]]
		return FileListResponse(items=items, page=page, page_size=page_size, total=total)

	def request_publish(
		self,
		context: AuthContext,
		file_id: str,
		*,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> PublishRequestResponse:
		record = self._file_repository.get_file_by_id(file_id)
		if record is None or record.organization_id != context.user.organization_id or record.status != Status.ACTIVE.value:
			raise NotFoundError(code="file_not_found", message="The requested file could not be found.")
		if record.owner_user_id != context.user.user_id:
			raise ForbiddenError(code="forbidden", message="You can only request publish for your own files.")
		if record.vault_type != VaultType.PRIVATE.value:
			raise ConflictError(code="not_private", message="Only private vault files can be requested for publish.")
		existing = self._file_repository.get_pending_publish_request(file_id)
		if existing is not None:
			raise ConflictError(code="request_exists", message="A pending publish request already exists for this file.")
		request = self._file_repository.create_publish_request(
			organization_id=context.user.organization_id,
			file_id=file_id,
			requester_user_id=context.user.user_id,
		)
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="request_publish",
			resource_type="file",
			resource_id=file_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return self._to_request_response(request, record)

	def list_publish_requests(
		self,
		context: AuthContext,
		*,
		status: str | None = None,
		page: int,
		page_size: int,
	) -> PublishRequestListResponse:
		if not can_approve_file(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only managers and admins can view publish requests.")
		requests = self._file_repository.list_publish_requests(
			context.user.organization_id,
			status=status,
		)
		total = len(requests)
		start = (page - 1) * page_size
		items = []
		for req in requests[start:start + page_size]:
			file_record = self._file_repository.get_file_by_id(req.file_id)
			if file_record is not None:
				items.append(self._to_request_response(req, file_record))
		return PublishRequestListResponse(items=items, total=total)

	def review_publish_request(
		self,
		context: AuthContext,
		request_id: str,
		*,
		approved: bool,
		note: str | None = None,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> PublishRequestResponse:
		if not can_approve_file(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only managers and admins can review publish requests.")
		req = self._file_repository.get_publish_request_by_id(request_id)
		if req is None or req.organization_id != context.user.organization_id:
			raise NotFoundError(code="request_not_found", message="The publish request could not be found.")
		if req.status != RequestStatus.PENDING.value:
			raise ConflictError(code="not_pending", message="Request is not in pending state.")
		now = now_utc()
		new_status = RequestStatus.APPROVED.value if approved else RequestStatus.REJECTED.value
		updated_req = self._file_repository.update_publish_request(
			request_id,
			status=new_status,
			reviewed_by_user_id=context.user.user_id,
			reviewed_at=now,
			review_note=note,
		)
		file_record = self._file_repository.get_file_by_id(req.file_id)
		if approved and file_record is not None:
			self._file_repository.update_publish_status(
				req.file_id,
				publish_status=PublishStatus.PUBLISHED.value,
				reviewed_by_user_id=context.user.user_id,
				reviewed_at=now,
				review_note=note,
			)
		action = "approve_publish_request" if approved else "reject_publish_request"
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action=action,
			resource_type="file",
			resource_id=req.file_id,
			result="success",
			reason=note,
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return self._to_request_response(updated_req, file_record)

	def admin_update_file(
		self,
		context: AuthContext,
		file_id: str,
		payload: FileAdminUpdateRequest,
		*,
		ip_address: str | None = None,
		user_agent: str | None = None,
	) -> FileItemResponse:
		if not can_manage_users(context.user.role):
			raise ForbiddenError(code="forbidden", message="Only admins can update file metadata.")
		record = self._file_repository.get_file_by_id(file_id)
		if record is None or record.organization_id != context.user.organization_id:
			raise NotFoundError(code="file_not_found", message="The requested file could not be found.")
		fields = {k: v for k, v in payload.model_dump().items() if v is not None}
		updated = self._file_repository.admin_update_file(file_id, fields=fields)
		self._audit_service.record_event(
			organization_id=context.user.organization_id,
			actor_user_id=context.user.user_id,
			action="admin_update_file",
			resource_type="file",
			resource_id=file_id,
			result="success",
			ip_address=ip_address,
			user_agent=user_agent,
		)
		return self._to_item_response(updated)

	def _resolve_visible_file(self, context: AuthContext, file_id: str, *, for_delete: bool = False) -> FileRecord:
		record = self._file_repository.get_file_by_id(file_id)
		if record is None or record.organization_id != context.user.organization_id or record.status != Status.ACTIVE.value:
			self._audit_service.record_event(
				organization_id=context.user.organization_id,
				actor_user_id=context.user.user_id,
				action="denied_access",
				resource_type="file",
				resource_id=file_id,
				result="denied",
				reason="file_not_found",
			)
			raise NotFoundError(code="file_not_found", message="The requested file could not be found.")
		if not can_view_file(
			context.user.role,
			actor_user_id=context.user.user_id,
			owner_user_id=record.owner_user_id,
			vault_type=record.vault_type,
			publish_status=record.publish_status,
		):
			self._audit_service.record_event(
				organization_id=context.user.organization_id,
				actor_user_id=context.user.user_id,
				action="denied_access",
				resource_type="file",
				resource_id=record.file_id,
				result="denied",
				reason="file_forbidden",
			)
			raise ForbiddenError(code="forbidden", message="You do not have permission to access this file.")
		if for_delete and not can_delete_file(context.user.role, actor_user_id=context.user.user_id, owner_user_id=record.owner_user_id):
			self._audit_service.record_event(
				organization_id=context.user.organization_id,
				actor_user_id=context.user.user_id,
				action="denied_access",
				resource_type="file",
				resource_id=record.file_id,
				result="denied",
				reason="delete_forbidden",
			)
			raise ForbiddenError(code="forbidden", message="You do not have permission to delete this file.")
		return record

	def _to_item_response(self, record: FileRecord) -> FileItemResponse:
		owner = self._auth_repository.get_user_by_id(record.owner_user_id)
		owner_name = owner.full_name if owner is not None else ""
		return FileItemResponse(
			file_id=record.file_id,
			organization_id=record.organization_id,
			owner_user_id=record.owner_user_id,
			owner_name=owner_name,
			uploaded_by_user_id=record.uploaded_by_user_id,
			original_name=record.original_name,
			mime_type=record.mime_type,
			size_bytes=record.size_bytes,
			sha256=record.sha256,
			encryption_algorithm=record.encryption_algorithm,
			vault_type=record.vault_type,
			publish_status=record.publish_status,
			reviewed_by_user_id=record.reviewed_by_user_id,
			reviewed_at=record.reviewed_at,
			review_note=record.review_note,
			status=record.status,
			created_at=record.created_at,
			updated_at=record.updated_at,
			deleted_at=record.deleted_at,
		)

	def _to_request_response(self, req, file_record) -> PublishRequestResponse:
		requester = self._auth_repository.get_user_by_id(req.requester_user_id)
		requester_name = requester.full_name if requester is not None else ""
		file_name = file_record.original_name if file_record is not None else ""
		return PublishRequestResponse(
			request_id=req.request_id,
			organization_id=req.organization_id,
			file_id=req.file_id,
			file_name=file_name,
			requester_user_id=req.requester_user_id,
			requester_name=requester_name,
			status=req.status,
			reviewed_by_user_id=req.reviewed_by_user_id,
			reviewed_at=req.reviewed_at,
			review_note=req.review_note,
			created_at=req.created_at,
			updated_at=req.updated_at,
		)
