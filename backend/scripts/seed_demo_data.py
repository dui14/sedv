"""Database seeding script for demo users.

Creates demo organization and three users with different roles:
- admin@demo.com (Admin role)
- manager@demo.com (Manager role)
- user@demo.com (User role)

Generates random secure passwords and saves them to docs/demo-credentials.md.
"""

import asyncio
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

from src.core.config.settings import get_settings
from src.core.security.passwords import hash_password
from src.domain.enums.roles import UserRole
from src.domain.enums.statuses import UserStatus
from src.utils.ids import generate_id


def generate_password(length: int = 16) -> str:
    """Generate a random secure password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password


async def seed_demo_data():
    """Seed demo organization and users."""
    settings = get_settings()

    print("🌱 Starting database seeding...")
    print(f"📊 Connecting to MongoDB: {settings.mongodb_database}")

    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_database]

    try:
        await client.admin.command("ping")
        print("✅ Connected to MongoDB successfully")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("\n💡 Make sure:")
        print("   1. MongoDB Atlas cluster is running")
        print("   2. SEDV_MONGODB_URI in .env is correct")
        print("   3. Your IP is whitelisted in Atlas Network Access")
        return

    organizations_collection = db["organizations"]
    users_collection = db["users"]

    now = datetime.now(timezone.utc)

    org_id = generate_id()
    org_slug = settings.demo_organization_slug

    existing_org = await organizations_collection.find_one({"slug": org_slug})

    if existing_org:
        print(f"📦 Organization '{settings.demo_organization_name}' already exists")
        org_id = existing_org["_id"]
    else:
        organization = {
            "_id": org_id,
            "name": settings.demo_organization_name,
            "slug": org_slug,
            "created_at": now,
            "updated_at": now,
        }
        await organizations_collection.insert_one(organization)
        print(f"✅ Created organization: {settings.demo_organization_name}")

    await organizations_collection.create_index("slug", unique=True)

    demo_users = [
        {
            "email": "admin@demo.com",
            "full_name": "Demo Admin",
            "role": UserRole.ADMIN,
        },
        {
            "email": "manager@demo.com",
            "full_name": "Demo Manager",
            "role": UserRole.MANAGER,
        },
        {
            "email": "user@demo.com",
            "full_name": "Demo User",
            "role": UserRole.USER,
        },
    ]

    credentials = []

    for user_data in demo_users:
        email = user_data["email"]
        existing_user = await users_collection.find_one({
            "organization_id": org_id,
            "email": email,
        })

        password = generate_password(16)
        password_hash = hash_password(password)

        if existing_user:
            await users_collection.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "password_hash": password_hash,
                        "updated_at": now,
                    }
                },
            )
            print(f"🔄 Updated user: {email} (password reset)")
        else:
            user = {
                "_id": generate_id(),
                "organization_id": org_id,
                "email": email,
                "full_name": user_data["full_name"],
                "password_hash": password_hash,
                "role": user_data["role"],
                "status": UserStatus.ACTIVE,
                "last_login_at": None,
                "created_at": now,
                "updated_at": now,
            }
            await users_collection.insert_one(user)
            print(f"✅ Created user: {email}")

        credentials.append({
            "email": email,
            "password": password,
            "role": user_data["role"],
            "full_name": user_data["full_name"],
        })

    await users_collection.create_index([("organization_id", 1), ("email", 1)], unique=True)
    await users_collection.create_index([("organization_id", 1), ("role", 1)])
    await users_collection.create_index([("organization_id", 1), ("status", 1)])

    print("\n✅ Database seeding completed!")
    print("\n" + "=" * 60)
    print("🔑 DEMO CREDENTIALS")
    print("=" * 60)

    for cred in credentials:
        print(f"\n{cred['full_name']} ({cred['role']})")
        print(f"  Email:    {cred['email']}")
        print(f"  Password: {cred['password']}")

    print("\n" + "=" * 60)

    docs_dir = Path(__file__).resolve().parents[2] / "docs"
    docs_dir.mkdir(exist_ok=True)
    credentials_file = docs_dir / "demo-credentials.md"

    with open(credentials_file, "w", encoding="utf-8") as f:
        f.write("# Demo Credentials\n\n")
        f.write("**⚠️ IMPORTANT**: These are randomly generated passwords. ")
        f.write("Save them securely or regenerate by running `npm run seed` again.\n\n")
        f.write(f"**Generated**: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write("---\n\n")

        for cred in credentials:
            f.write(f"## {cred['full_name']} ({cred['role']})\n\n")
            f.write(f"- **Email**: `{cred['email']}`\n")
            f.write(f"- **Password**: `{cred['password']}`\n")
            f.write(f"- **Role**: {cred['role']}\n\n")

        f.write("---\n\n")
        f.write("## Role Permissions\n\n")
        f.write("### Admin\n")
        f.write("- View all files in the organization\n")
        f.write("- Upload, download, delete any file\n")
        f.write("- View all audit logs\n")
        f.write("- Full system access\n\n")

        f.write("### Manager\n")
        f.write("- View all files in the organization\n")
        f.write("- Upload, download, delete any file\n")
        f.write("- View audit logs (limited scope)\n")
        f.write("- Cannot manage users or roles\n\n")

        f.write("### User\n")
        f.write("- View only their own files\n")
        f.write("- Upload, download, delete own files\n")
        f.write("- View own audit logs only\n")
        f.write("- No access to other users' files\n\n")

        f.write("---\n\n")
        f.write("## Usage\n\n")
        f.write("1. Start the application: `npm run dev`\n")
        f.write("2. Open http://localhost:3000\n")
        f.write("3. Log in with any of the credentials above\n")
        f.write("4. Test different role permissions\n\n")

        f.write("To regenerate credentials:\n")
        f.write("```bash\n")
        f.write("npm run seed\n")
        f.write("```\n")

    print(f"\n💾 Credentials saved to: {credentials_file}")
    print("\n🚀 Ready to start! Run: npm run dev")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
