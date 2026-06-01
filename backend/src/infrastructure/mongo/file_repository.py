from __future__ import annotations

from datetime import datetime
import re

from ...domain.entities.file import FileRecord, PublishRequestRecord
from ...utils.datetime import ensure_utc, now_utc
from ...utils.errors import ConflictError, NotFoundError
from ...utils.ids import new_id
from .client import MongoDatabaseClient
from .collections import FILES_COLLECTION, PUBLISH_REQUESTS_COLLECTION

try:
	from pymongo import DESCENDING, ReturnDocument
	from pymongo.errors import DuplicateKeyError
except ImportError:  # pragma: no cover - dependency is validated at startup
	DESCENDING = -1
	ReturnDocument = None
	DuplicateKeyError = Exception


def _file_to_document(record: FileRecord) -> dict:
	return {
		"_id": record.file_id,
		"organization_id": record.organization_id,
		"owner_user_id": record.owner_user_id,
		"uploaded_by_user_id": record.uploaded_by_user_id,
		"original_name": record.original_name,
		"storage_name": record.storage_name,
		"storage_path": record.storage_path,
		"mime_type": record.mime_type,
		"size_bytes": record.size_bytes,
		"sha256": record.sha256,
		"encryption_algorithm": record.encryption_algorithm,
		"encryption_iv": record.encryption_iv,
		"encryption_key_version": record.encryption_key_version,
		"vault_type": record.vault_type,
		"publish_status": record.publish_status,
		"reviewed_by_user_id": record.reviewed_by_user_id,
		"reviewed_at": record.reviewed_at,
		"review_note": record.review_note,
		"status": record.status,
		"deleted_at": record.deleted_at,
		"created_at": record.created_at,
		"updated_at": record.updated_at,
	}


def _file_from_document(document: dict) -> FileRecord:
	return FileRecord(
		file_id=str(document["_id"]),
		organization_id=document["organization_id"],
		owner_user_id=document["owner_user_id"],
		uploaded_by_user_id=document["uploaded_by_user_id"],
		original_name=document["original_name"],
		storage_name=document["storage_name"],
		storage_path=document["storage_path"],
		mime_type=document["mime_type"],
		size_bytes=document["size_bytes"],
		sha256=document["sha256"],
		encryption_algorithm=document["encryption_algorithm"],
		encryption_iv=document["encryption_iv"],
		encryption_key_version=document["encryption_key_version"],
		vault_type=document.get("vault_type", "general"),
		publish_status=document.get("publish_status", "published"),
		reviewed_by_user_id=document.get("reviewed_by_user_id"),
		reviewed_at=ensure_utc(document.get("reviewed_at")),
		review_note=document.get("review_note"),
		status=document["status"],
		deleted_at=ensure_utc(document.get("deleted_at")),
		created_at=ensure_utc(document["created_at"]),
		updated_at=ensure_utc(document["updated_at"]),
	)


def _publish_request_from_document(document: dict) -> PublishRequestRecord:
	return PublishRequestRecord(
		request_id=str(document["_id"]),
		organization_id=document["organization_id"],
		file_id=document["file_id"],
		requester_user_id=document["requester_user_id"],
		status=document["status"],
		reviewed_by_user_id=document.get("reviewed_by_user_id"),
		reviewed_at=ensure_utc(document.get("reviewed_at")),
		review_note=document.get("review_note"),
		created_at=ensure_utc(document["created_at"]),
		updated_at=ensure_utc(document["updated_at"]),
	)


class FileRepository:
	def __init__(self, client: MongoDatabaseClient) -> None:
		self._files = client.database[FILES_COLLECTION]
		self._requests = client.database[PUBLISH_REQUESTS_COLLECTION]

	def create_file(self, record: FileRecord) -> FileRecord:
		try:
			self._files.insert_one(_file_to_document(record))
		except DuplicateKeyError as exc:
			raise ConflictError(code="file_conflict", message="A file with this identifier or storage name already exists.") from exc
		return record

	def get_file_by_id(self, file_id: str) -> FileRecord | None:
		document = self._files.find_one({"_id": file_id})
		return _file_from_document(document) if document is not None else None

	def list_files(
		self,
		organization_id: str,
		*,
		owner_user_id: str | None = None,
		vault_type: str | None = None,
		publish_status: str | None = None,
		search: str | None = None,
		include_deleted: bool = False,
	) -> list[FileRecord]:
		term = search.lower().strip() if search else None
		query: dict = {"organization_id": organization_id}
		if not include_deleted:
			query["status"] = "active"
		if owner_user_id is not None:
			query["owner_user_id"] = owner_user_id
		if vault_type is not None:
			query["vault_type"] = vault_type
		if publish_status is not None:
			query["publish_status"] = publish_status
		if term:
			pattern = re.compile(re.escape(term), re.IGNORECASE)
			query["$or"] = [
				{"original_name": pattern},
				{"mime_type": pattern},
				{"storage_name": pattern},
			]
		return [_file_from_document(document) for document in self._files.find(query).sort("created_at", DESCENDING)]

	def mark_deleted(self, file_id: str, deleted_at: datetime) -> FileRecord:
		document = self._files.find_one_and_update(
			{"_id": file_id},
			{"$set": {"status": "deleted", "deleted_at": deleted_at, "updated_at": deleted_at}},
			return_document=ReturnDocument.AFTER,
		)
		if document is None:
			raise NotFoundError(code="file_not_found", message="The requested file could not be found.")
		return _file_from_document(document)

	def update_publish_status(
		self,
		file_id: str,
		*,
		publish_status: str,
		reviewed_by_user_id: str,
		reviewed_at: datetime,
		review_note: str | None,
	) -> FileRecord:
		document = self._files.find_one_and_update(
			{"_id": file_id},
			{
				"$set": {
					"publish_status": publish_status,
					"reviewed_by_user_id": reviewed_by_user_id,
					"reviewed_at": reviewed_at,
					"review_note": review_note,
					"updated_at": reviewed_at,
				}
			},
			return_document=ReturnDocument.AFTER,
		)
		if document is None:
			raise NotFoundError(code="file_not_found", message="The requested file could not be found.")
		return _file_from_document(document)

	def admin_update_file(self, file_id: str, *, fields: dict) -> FileRecord:
		fields["updated_at"] = now_utc()
		document = self._files.find_one_and_update(
			{"_id": file_id},
			{"$set": fields},
			return_document=ReturnDocument.AFTER,
		)
		if document is None:
			raise NotFoundError(code="file_not_found", message="The requested file could not be found.")
		return _file_from_document(document)

	def create_publish_request(
		self,
		*,
		organization_id: str,
		file_id: str,
		requester_user_id: str,
	) -> PublishRequestRecord:
		now = now_utc()
		document = {
			"_id": new_id(),
			"organization_id": organization_id,
			"file_id": file_id,
			"requester_user_id": requester_user_id,
			"status": "pending",
			"reviewed_by_user_id": None,
			"reviewed_at": None,
			"review_note": None,
			"created_at": now,
			"updated_at": now,
		}
		self._requests.insert_one(document)
		return _publish_request_from_document(document)

	def get_publish_request_by_id(self, request_id: str) -> PublishRequestRecord | None:
		document = self._requests.find_one({"_id": request_id})
		return _publish_request_from_document(document) if document is not None else None

	def get_pending_publish_request(self, file_id: str) -> PublishRequestRecord | None:
		document = self._requests.find_one({"file_id": file_id, "status": "pending"})
		return _publish_request_from_document(document) if document is not None else None

	def list_publish_requests(
		self,
		organization_id: str,
		*,
		status: str | None = None,
	) -> list[PublishRequestRecord]:
		query: dict = {"organization_id": organization_id}
		if status is not None:
			query["status"] = status
		return [_publish_request_from_document(d) for d in self._requests.find(query).sort("created_at", DESCENDING)]

	def update_publish_request(
		self,
		request_id: str,
		*,
		status: str,
		reviewed_by_user_id: str,
		reviewed_at: datetime,
		review_note: str | None,
	) -> PublishRequestRecord:
		document = self._requests.find_one_and_update(
			{"_id": request_id},
			{
				"$set": {
					"status": status,
					"reviewed_by_user_id": reviewed_by_user_id,
					"reviewed_at": reviewed_at,
					"review_note": review_note,
					"updated_at": reviewed_at,
				}
			},
			return_document=ReturnDocument.AFTER,
		)
		if document is None:
			raise NotFoundError(code="request_not_found", message="The publish request could not be found.")
		return _publish_request_from_document(document)
