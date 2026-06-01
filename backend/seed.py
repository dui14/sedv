"""
Seed script: drops all users/files/audit_logs/auth_sessions/publish_requests,
then creates 2 admins, 6 managers, 24 regular users.
Run from the project root:
  cd backend
  python seed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pymongo import MongoClient
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.core.security.passwords import hash_password
import uuid
from datetime import datetime, timezone


class SeedSettings(BaseSettings):
	model_config = SettingsConfigDict(
		env_prefix="SEDV_",
		env_file=ROOT_ENV,
		env_file_encoding="utf-8",
		extra="ignore",
	)
	mongodb_uri: str = "mongodb://localhost:27017"
	mongodb_database: str = "sedv"
	demo_organization_slug: str = "demo-org"
	demo_organization_name: str = "Demo Organization"
	password_min_length: int = 8


def new_id() -> str:
	return str(uuid.uuid4()).replace("-", "")


def now_utc() -> datetime:
	return datetime.now(timezone.utc)


def run() -> None:
	settings = SeedSettings()
	client = MongoClient(settings.mongodb_uri)
	db = client[settings.mongodb_database]

	org_col = db["organizations"]
	user_col = db["users"]
	file_col = db["files"]
	audit_col = db["audit_logs"]
	session_col = db["auth_sessions"]
	requests_col = db["publish_requests"]

	existing_org = org_col.find_one({"slug": settings.demo_organization_slug})
	if existing_org is None:
		now = now_utc()
		org_doc = {
			"_id": new_id(),
			"name": settings.demo_organization_name,
			"slug": settings.demo_organization_slug,
			"created_at": now,
			"updated_at": now,
		}
		org_col.insert_one(org_doc)
		org_id = org_doc["_id"]
		print(f"Created organization: {settings.demo_organization_name}")
	else:
		org_id = str(existing_org["_id"])
		print(f"Using existing organization: {existing_org['name']} ({org_id})")

	user_col.delete_many({"organization_id": org_id})
	file_col.delete_many({"organization_id": org_id})
	audit_col.delete_many({"organization_id": org_id})
	session_col.delete_many({"organization_id": org_id})
	requests_col.delete_many({"organization_id": org_id})
	print("Cleared existing data for organization.")

	users_to_create = []

	for i in range(1, 3):
		users_to_create.append({
			"email": f"admin{i}@company.com",
			"full_name": f"Admin User {i}",
			"password": "Admin@123",
			"role": "admin",
		})

	for i in range(1, 7):
		users_to_create.append({
			"email": f"manager{i}@company.com",
			"full_name": f"Manager User {i}",
			"password": "Manager@123",
			"role": "manager",
		})

	for i in range(1, 25):
		users_to_create.append({
			"email": f"user{i}@company.com",
			"full_name": f"Regular User {i}",
			"password": "User@123",
			"role": "user",
		})

	now = now_utc()
	for u in users_to_create:
		doc = {
			"_id": new_id(),
			"organization_id": org_id,
			"email": u["email"],
			"full_name": u["full_name"],
			"password_hash": hash_password(u["password"]),
			"role": u["role"],
			"status": "active",
			"last_login_at": None,
			"created_at": now,
			"updated_at": now,
		}
		user_col.insert_one(doc)
		print(f"  [{u['role']:7s}] {u['email']:35s}  pass: {u['password']}")

	print(f"\nSeeded {len(users_to_create)} users total.")
	print(f"  - 2 admins   (admin1@company.com … admin2@company.com, Admin@123)")
	print(f"  - 6 managers (manager1@company.com … manager6@company.com, Manager@123)")
	print(f"  - 24 users   (user1@company.com … user24@company.com, User@123)")
	client.close()


if __name__ == "__main__":
	run()
