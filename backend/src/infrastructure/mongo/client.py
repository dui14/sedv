from __future__ import annotations

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database

from .collections import (
	AUDIT_LOGS_COLLECTION,
	AUTH_SESSIONS_COLLECTION,
	FILES_COLLECTION,
	ORGANIZATIONS_COLLECTION,
	USERS_COLLECTION,
)


class MongoDatabaseClient:
	def __init__(self, uri: str, database_name: str) -> None:
		self._client: MongoClient = MongoClient(uri, serverSelectionTimeoutMS=5000)
		self.database: Database = self._client[database_name]
		self._client.admin.command("ping")
		self._ensure_indexes()

	def close(self) -> None:
		self._client.close()

	def _ensure_indexes(self) -> None:
		self.database[ORGANIZATIONS_COLLECTION].create_index("slug", unique=True)

		users = self.database[USERS_COLLECTION]
		users.create_index([("organization_id", ASCENDING), ("email", ASCENDING)], unique=True)
		users.create_index([("organization_id", ASCENDING), ("role", ASCENDING)])
		users.create_index([("organization_id", ASCENDING), ("status", ASCENDING)])

		sessions = self.database[AUTH_SESSIONS_COLLECTION]
		sessions.create_index("jti", unique=True)
		sessions.create_index([("user_id", ASCENDING), ("expires_at", ASCENDING)])
		sessions.create_index([("organization_id", ASCENDING), ("expires_at", ASCENDING)])

		files = self.database[FILES_COLLECTION]
		files.create_index("storage_name", unique=True)
		files.create_index([("organization_id", ASCENDING), ("created_at", DESCENDING)])
		files.create_index([("organization_id", ASCENDING), ("owner_user_id", ASCENDING), ("created_at", DESCENDING)])
		files.create_index([("organization_id", ASCENDING), ("original_name", ASCENDING)])
		files.create_index(
			[("organization_id", ASCENDING), ("status", ASCENDING)],
			partialFilterExpression={"status": "active"},
		)

		audit_logs = self.database[AUDIT_LOGS_COLLECTION]
		audit_logs.create_index([("organization_id", ASCENDING), ("created_at", DESCENDING)])
		audit_logs.create_index([("actor_user_id", ASCENDING), ("created_at", DESCENDING)])
		audit_logs.create_index([("organization_id", ASCENDING), ("action", ASCENDING), ("created_at", DESCENDING)])
		audit_logs.create_index(
			[
				("organization_id", ASCENDING),
				("resource_type", ASCENDING),
				("resource_id", ASCENDING),
				("created_at", DESCENDING),
			]
		)
