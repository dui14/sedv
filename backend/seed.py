"""
Seed script for companyABC demo data.

Drops all users/files/audit_logs/auth_sessions/publish_requests for the org,
then seeds:
  - 1 company super-admin
  - 2 floor admins  (Floor 1: Business Operations, Floor 2: Engineering)
  - 6 managers      (3 per floor)
  - 24 users        (4 per manager)

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
    demo_organization_slug: str = "companyabc"
    demo_organization_name: str = "companyABC"
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
    floor_col = db["floors"]

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
    floor_col.delete_many({"organization_id": org_id})
    print("Cleared existing data for organization.")

    now = now_utc()

    floor1_id = new_id()
    floor2_id = new_id()
    floor_col.insert_many([
        {
            "_id": floor1_id,
            "organization_id": org_id,
            "name": "Business Operations",
            "slug": "floor-1-biz-ops",
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": floor2_id,
            "organization_id": org_id,
            "name": "Engineering",
            "slug": "floor-2-engineering",
            "created_at": now,
            "updated_at": now,
        },
    ])
    print("Created 2 floors.")

    def insert_user(
        email: str,
        full_name: str,
        password: str,
        role: str,
        floor_id: str | None = None,
        manager_id: str | None = None,
        department: str | None = None,
    ) -> str:
        uid = new_id()
        doc = {
            "_id": uid,
            "organization_id": org_id,
            "email": email,
            "full_name": full_name,
            "password_hash": hash_password(password),
            "role": role,
            "status": "active",
            "floor_id": floor_id,
            "manager_id": manager_id,
            "department": department,
            "last_login_at": None,
            "created_at": now,
            "updated_at": now,
        }
        user_col.insert_one(doc)
        dept_label = f" [{department}]" if department else ""
        print(f"  [{role:8s}]{dept_label:12s} {email:45s}  pass: {password}")
        return uid

    print("\n--- COMPANY ---")
    insert_user(
        email="company@companyabc.com",
        full_name="David Chen",
        password="Company@123",
        role="company",
    )

    print("\n--- FLOOR 1: Business Operations ---")
    admin1_id = insert_user(
        email="admin.biz@companyabc.com",
        full_name="Sarah Mitchell",
        password="Admin@123",
        role="admin",
        floor_id=floor1_id,
    )

    print("  [Floor 1 > Sales]")
    mgr_sales_id = insert_user(
        email="sales.manager@companyabc.com",
        full_name="James Thornton",
        password="Manager@123",
        role="manager",
        floor_id=floor1_id,
        department="Sales",
    )
    for i in range(1, 5):
        insert_user(
            email=f"sales{i:02d}@companyabc.com",
            full_name=f"Sales Representative {i:02d}",
            password="User@123",
            role="user",
            floor_id=floor1_id,
            manager_id=mgr_sales_id,
            department="Sales",
        )

    print("  [Floor 1 > Operations]")
    mgr_ops_id = insert_user(
        email="ops.manager@companyabc.com",
        full_name="Linda Park",
        password="Manager@123",
        role="manager",
        floor_id=floor1_id,
        department="Operations",
    )
    for i in range(1, 5):
        insert_user(
            email=f"ops{i:02d}@companyabc.com",
            full_name=f"Operations Analyst {i:02d}",
            password="User@123",
            role="user",
            floor_id=floor1_id,
            manager_id=mgr_ops_id,
            department="Operations",
        )

    print("  [Floor 1 > Support]")
    mgr_support_id = insert_user(
        email="support.manager@companyabc.com",
        full_name="Kevin Walsh",
        password="Manager@123",
        role="manager",
        floor_id=floor1_id,
        department="Support",
    )
    for i in range(1, 5):
        insert_user(
            email=f"support{i:02d}@companyabc.com",
            full_name=f"Support Specialist {i:02d}",
            password="User@123",
            role="user",
            floor_id=floor1_id,
            manager_id=mgr_support_id,
            department="Support",
        )

    print("\n--- FLOOR 2: Engineering ---")
    admin2_id = insert_user(
        email="admin.eng@companyabc.com",
        full_name="Mark Rivera",
        password="Admin@123",
        role="admin",
        floor_id=floor2_id,
    )

    print("  [Floor 2 > Backend]")
    mgr_backend_id = insert_user(
        email="backend.manager@companyabc.com",
        full_name="Priya Sharma",
        password="Manager@123",
        role="manager",
        floor_id=floor2_id,
        department="BE",
    )
    for i in range(1, 5):
        insert_user(
            email=f"backend{i:02d}@companyabc.com",
            full_name=f"Backend Engineer {i:02d}",
            password="User@123",
            role="user",
            floor_id=floor2_id,
            manager_id=mgr_backend_id,
            department="BE",
        )

    print("  [Floor 2 > Frontend]")
    mgr_frontend_id = insert_user(
        email="frontend.manager@companyabc.com",
        full_name="Alex Nguyen",
        password="Manager@123",
        role="manager",
        floor_id=floor2_id,
        department="FE",
    )
    for i in range(1, 5):
        insert_user(
            email=f"frontend{i:02d}@companyabc.com",
            full_name=f"Frontend Engineer {i:02d}",
            password="User@123",
            role="user",
            floor_id=floor2_id,
            manager_id=mgr_frontend_id,
            department="FE",
        )

    print("  [Floor 2 > Product]")
    mgr_product_id = insert_user(
        email="product.manager@companyabc.com",
        full_name="Rachel Kim",
        password="Manager@123",
        role="manager",
        floor_id=floor2_id,
        department="Product",
    )
    for i in range(1, 5):
        insert_user(
            email=f"product{i:02d}@companyabc.com",
            full_name=f"Product Specialist {i:02d}",
            password="User@123",
            role="user",
            floor_id=floor2_id,
            manager_id=mgr_product_id,
            department="Product",
        )

    print("\nSeeded 33 accounts total.")
    print("  - 1 company  (company@companyabc.com, Company@123)")
    print("  - 2 admins   (admin.biz / admin.eng @companyabc.com, Admin@123)")
    print("  - 6 managers (sales/ops/support/backend/frontend/product.manager@, Manager@123)")
    print("  - 24 users   (sales01-04 / ops01-04 / support01-04 / backend01-04 / frontend01-04 / product01-04 @, User@123)")
    client.close()


if __name__ == "__main__":
    run()
