from __future__ import annotations

from datetime import datetime

from ...core.config.settings import Settings
from ...domain.entities.auth_session import AuthSessionRecord
from ...domain.entities.organization import OrganizationRecord
from ...domain.entities.user import UserRecord
from ...domain.enums.statuses import Status
from ...utils.datetime import ensure_utc, now_utc
from ...utils.errors import ConflictError, NotFoundError
from ...utils.ids import new_id
from .client import MongoDatabaseClient
from .collections import AUTH_SESSIONS_COLLECTION, ORGANIZATIONS_COLLECTION, USERS_COLLECTION

try:
	from pymongo import ReturnDocument
	from pymongo.errors import DuplicateKeyError
except ImportError:  # pragma: no cover - dependency is validated at startup
	ReturnDocument = None
	DuplicateKeyError = Exception


def _organization_from_document(document: dict) -> OrganizationRecord:
	return OrganizationRecord(
		organization_id=str(document["_id"]),
		name=document["name"],
		slug=document["slug"],
		created_at=ensure_utc(document["created_at"]),
		updated_at=ensure_utc(document["updated_at"]),
	)


def _user_from_document(document: dict) -> UserRecord:
	return UserRecord(
		user_id=str(document["_id"]),
		organization_id=document["organization_id"],
		email=document["email"],
		full_name=document["full_name"],
		password_hash=document.get("password_hash"),
		role=document["role"],
		status=document["status"],
		last_login_at=ensure_utc(document.get("last_login_at")),
		created_at=ensure_utc(document["created_at"]),
		updated_at=ensure_utc(document["updated_at"]),
	)


def _session_from_document(document: dict) -> AuthSessionRecord:
	return AuthSessionRecord(
		session_id=str(document["_id"]),
		organization_id=document["organization_id"],
		user_id=document["user_id"],
		jti=document["jti"],
		issued_at=ensure_utc(document["issued_at"]),
		expires_at=ensure_utc(document["expires_at"]),
		revoked_at=ensure_utc(document.get("revoked_at")),
		created_at=ensure_utc(document["created_at"]),
	)


class AuthRepository:
    def __init__(self, client: MongoDatabaseClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings
        self._organizations = client.database[ORGANIZATIONS_COLLECTION]
        self._users = client.database[USERS_COLLECTION]
        self._sessions = client.database[AUTH_SESSIONS_COLLECTION]
        self._demo_organization = self._ensure_demo_organization()

    def _ensure_demo_organization(self) -> OrganizationRecord:
        existing = self._organizations.find_one({"slug": self._settings.demo_organization_slug})
        if existing is not None:
            return _organization_from_document(existing)
        now = now_utc()
        document = {
            "_id": new_id(),
            "name": self._settings.demo_organization_name,
            "slug": self._settings.demo_organization_slug,
            "created_at": now,
            "updated_at": now,
        }
        try:
            self._organizations.insert_one(document)
        except DuplicateKeyError:
            document = self._organizations.find_one({"slug": self._settings.demo_organization_slug})
            if document is None:
                raise
        return _organization_from_document(document)

    def get_demo_organization(self) -> OrganizationRecord:
        return self._demo_organization

    def get_user_by_email(self, organization_id: str, email: str) -> UserRecord | None:
        document = self._users.find_one({"organization_id": organization_id, "email": email})
        return _user_from_document(document) if document is not None else None

    def get_user_by_id(self, user_id: str) -> UserRecord | None:
        document = self._users.find_one({"_id": user_id})
        return _user_from_document(document) if document is not None else None

    def create_user(
        self,
        *,
        organization_id: str,
        email: str,
        full_name: str,
        password_hash: str | None,
        role: str = "user",
        status: str = Status.ACTIVE.value,
    ) -> UserRecord:
        now = now_utc()
        document = {
            "_id": new_id(),
            "organization_id": organization_id,
            "email": email,
            "full_name": full_name,
            "password_hash": password_hash,
            "role": role,
            "status": status,
            "last_login_at": None,
            "created_at": now,
            "updated_at": now,
        }
        try:
            self._users.insert_one(document)
        except DuplicateKeyError as exc:
            raise ConflictError(code="email_already_exists", message="A user with this email already exists.") from exc
        return _user_from_document(document)

    def update_last_login(self, user_id: str, login_at: datetime) -> UserRecord:
        document = self._users.find_one_and_update(
            {"_id": user_id},
            {"$set": {"last_login_at": login_at, "updated_at": login_at}},
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
        return _user_from_document(document)

    def create_session(
        self,
        *,
        organization_id: str,
        user_id: str,
        jti: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> AuthSessionRecord:
        document = {
            "_id": new_id(),
            "organization_id": organization_id,
            "user_id": user_id,
            "jti": jti,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "revoked_at": None,
            "created_at": issued_at,
        }
        try:
            self._sessions.insert_one(document)
        except DuplicateKeyError as exc:
            raise ConflictError(code="session_conflict", message="A session with this token identifier already exists.") from exc
        return _session_from_document(document)

    def get_session_by_jti(self, jti: str) -> AuthSessionRecord | None:
        document = self._sessions.find_one({"jti": jti})
        return _session_from_document(document) if document is not None else None

    def revoke_session(self, jti: str, revoked_at: datetime) -> AuthSessionRecord:
        document = self._sessions.find_one_and_update(
            {"jti": jti},
            {"$set": {"revoked_at": revoked_at}},
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            raise NotFoundError(code="session_not_found", message="The requested session could not be found.")
        return _session_from_document(document)

    def list_users(
        self,
        organization_id: str,
        *,
        role: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list:
        import re as _re
        query: dict = {"organization_id": organization_id}
        if role is not None:
            query["role"] = role
        if status is not None:
            query["status"] = status
        if search:
            pattern = _re.compile(_re.escape(search), _re.IGNORECASE)
            query["$or"] = [
                {"full_name": pattern},
                {"email": pattern},
            ]
        return [_user_from_document(d) for d in self._users.find(query).sort("created_at", -1)]

    def update_user(
        self,
        user_id: str,
        *,
        full_name: str | None = None,
        role: str | None = None,
        status: str | None = None,
    ):
        fields: dict = {"updated_at": now_utc()}
        if full_name is not None:
            fields["full_name"] = full_name
        if role is not None:
            fields["role"] = role
        if status is not None:
            fields["status"] = status
        document = self._users.find_one_and_update(
            {"_id": user_id},
            {"$set": fields},
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
        return _user_from_document(document)

    def delete_user(self, user_id: str) -> None:
        result = self._users.delete_one({"_id": user_id})
        if result.deleted_count == 0:
            raise NotFoundError(code="user_not_found", message="The requested user could not be found.")
