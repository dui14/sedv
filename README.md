# Secure Enterprise Data Vault

SEDV is a local demo web app for secure enterprise file storage. It shows how authentication, role-based access control, encrypted file handling, and audit logging work together in one simple flow.

Core features:
- Email/password authentication with short-lived JWT sessions
- Role-based access for Admin, Manager, and User
- Encrypted file upload, storage, download, and deletion
- Permission-aware file listing and search
- Audit logs for security-sensitive actions

Setup:
1. Read [docs/development-setup.md](docs/development-setup.md) for local setup.
2. If you need MongoDB Atlas, follow [docs/mongodb-setup.md](docs/mongodb-setup.md).
3. Use [docs/list.txt](docs/list.txt) for demo test accounts and passwords.
4. Copy `.env.example` and `frontend/.env.local.example`, then fill in the required values.
5. Seed demo data with `cd backend && python seed.py`.
6. Start the app with `npm run dev`.
7. Read [docs/architecture.md](docs/architecture.md) for architectural details.

Frontend: `http://localhost:3000`
Backend: `http://localhost:8000`