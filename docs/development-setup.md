# Development Setup Guide

Complete guide to set up the Secure Enterprise Data Vault development environment.

## Prerequisites

### Required Software

1. **Node.js 18+** and **npm 9+**
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify: `node --version` and `npm --version`

2. **Python 3.12+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python --version`

3. **Git**
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify: `git --version`

### Required Accounts

1. **MongoDB Atlas** (free tier)
   - Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - See [mongodb-setup.md](./mongodb-setup.md) for detailed setup


## Quick Start (5 minutes)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd sedv

# 2. Install all dependencies
npm run install:all

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your MongoDB Atlas URI and other secrets

# 4. Seed demo users
npm run seed

# 5. Start both frontend and backend
npm run dev
```

Open http://localhost:3000 and log in with credentials from `docs/demo-credentials.md`.

---

## Detailed Setup

### Step 1: Install Dependencies

**Root dependencies** (for dev orchestration):
```bash
npm install
```

**Frontend dependencies**:
```bash
cd frontend
npm install
cd ..
```

**Backend dependencies**:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

---

### Step 2: Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and configure the following **required** variables:

```bash
# MongoDB Atlas connection string (REQUIRED)
SEDV_MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority

# JWT secret (REQUIRED - generate a random string)
SEDV_JWT_SECRET=<generate-random-32-char-string>

# File encryption key seed (REQUIRED - generate a random string)
SEDV_FILE_ENCRYPTION_KEY_SEED=<generate-random-32-char-string>
```

See [environment-variables.md](./environment-variables.md) for complete reference.

---

### Step 3: Set Up MongoDB Atlas

Follow the detailed guide in [mongodb-setup.md](./mongodb-setup.md).

**Quick checklist**:
- ✅ Create free cluster
- ✅ Create database user
- ✅ Add your IP to network access
- ✅ Get connection string
- ✅ Update `SEDV_MONGODB_URI` in `.env`

---

### Step 4: Seed Demo Data

Create demo users (admin, manager, user) with random passwords:

```bash
npm run seed
```

This will:
- Create the demo organization
- Create 3 users with different roles
- Generate random secure passwords
- Save credentials to `docs/demo-credentials.md`

**Important**: Save the generated passwords! They're printed to console and written to `docs/demo-credentials.md`.

---

### Step 5: Start Development Servers

**Option A: Start both servers together** (recommended):
```bash
npm run dev
```

This starts:
- Frontend on http://localhost:3000
- Backend on http://localhost:8000

**Option B: Start servers individually**:
```bash
# Terminal 1 - Frontend
npm run dev:frontend

# Terminal 2 - Backend
npm run dev:backend
```

---

## Verify Setup

1. **Frontend**: Open http://localhost:3000
   - Should see login screen
   - No console errors

2. **Backend**: Open http://localhost:8000/api/health
   - Should return: `{"status": "healthy"}`

3. **MongoDB**: Check connection
   - Backend logs should show: "Connected to MongoDB"
   - No connection errors

4. **Login**: Use credentials from `docs/demo-credentials.md`
   - Login as admin@demo.com
   - Should see vault dashboard

---

## Common Issues

### "Cannot connect to MongoDB"

**Solution**:
- Verify `SEDV_MONGODB_URI` in `.env` is correct
- Check MongoDB Atlas network access allows your IP
- Ensure database user credentials are correct

### "Module not found" errors

**Solution**:
```bash
# Reinstall all dependencies
npm run install:all

# Backend: activate venv and reinstall
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### "Port 3000 already in use"

**Solution**:
```bash
# Kill process on port 3000
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:3000 | xargs kill -9
```

### "Port 8000 already in use"

**Solution**:
```bash
# Kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

---

## Development Workflow

### Making Changes

1. **Frontend changes**: Hot reload automatic (Next.js)
2. **Backend changes**: Auto-reload enabled (uvicorn --reload)
3. **Environment changes**: Restart servers

### Running Tests

```bash
# Frontend tests (when implemented)
cd frontend
npm test

# Backend tests (when implemented)
cd backend
pytest
```

### Building for Production

```bash
# Frontend production build
npm run build:frontend

# Backend runs same code (FastAPI)
```

---

## Next Steps

- Read [architecture-overview.md](./architecture-overview.md) to understand the system
- Check [environment-variables.md](./environment-variables.md) for all config options
- Review [mongodb-setup.md](./mongodb-setup.md) for database details
- See [setup-mcp.md](./setup-mcp.md) to configure MCP servers for enhanced agent capabilities

---

## Getting Help

- Check existing documentation in `docs/`
- Review error messages carefully
- Ensure all prerequisites are installed
- Verify environment variables are set correctly
