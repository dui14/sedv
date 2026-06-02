# MongoDB Atlas Setup Guide

This guide walks you through setting up a free MongoDB Atlas cluster for the Secure Enterprise Data Vault demo.

## Why MongoDB Atlas?

MongoDB Atlas is a fully managed cloud database service that provides:
- **Free tier**: 512 MB storage, perfect for demos
- **No local installation**: No Docker or MongoDB server needed
- **Automatic backups**: Built-in data protection
- **Global availability**: Access from anywhere
- **Easy scaling**: Upgrade when needed

---

## Step-by-Step Setup

### Step 1: Create MongoDB Atlas Account

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Click **"Try Free"** or **"Sign Up"**
3. Sign up with:
   - Email and password, OR
   - Google account, OR
   - GitHub account
4. Verify your email if required

---

### Step 2: Create a Free Cluster

1. After login, you'll see **"Create a deployment"** or **"Build a Database"**
2. Choose **"M0 FREE"** tier:
   - Storage: 512 MB
   - RA
   - Cost: **FREE forever**
3. Select a cloud provider and region:
   - **Provider**: AWS, Google Cloud, or Azure (any works)
   - **Region**: Choose closest tM: Sharedo your location for better performance
   - Example: `AWS / Singapore (ap-southeast-1)`
4. Cluster name: Leave default or name it `sedv-demo`
5. Click **"Create Deployment"** or **"Create Cluster"**
6. Wait 1-3 minutes for cluster creation

---

### Step 3: Create Database User

You'll see a security quickstart screen:

1. **Username**: Enter a username (e.g., `sedv_user`)
2. **Password**: Click **"Autogenerate Secure Password"** or create your own
   - ⚠️ **IMPORTANT**: Copy and save this password! You'll need it for the connection string
   - Avoid special characters like `@`, `:`, `/` in password (they cause connection issues)
3. Click **"Create User"**

**Alternative path** (if you skipped quickstart):
1. Go to **"Database Access"** in left sidebar
2. Click **"Add New Database User"**
3. Authentication Method: **"Password"**
4. Username and password as above
5. Database User Privileges: **"Read and write to any database"**
6. Click **"Add User"**

---

### Step 4: Configure Network Access

Allow your computer to connect to the database:

1. You'll see **"Where would you like to connect from?"** screen
2. Choose **"My Local Environment"**
3. Click **"Add My Current IP Address"**
   - This automatically adds your current IP
   - Description: `My Development Machine` (optional)
4. Click **"Finish and Close"**

**Alternative path** (if you skipped quickstart):
1. Go to **"Network Access"** in left sidebar
2. Click **"Add IP Address"**
3. Options:
   - **"Add Current IP Address"** (recommended for security)
   - **"Allow Access from Anywhere"** (`0.0.0.0/0`) - less secure but works from any network
4. Click **"Confirm"**

⚠️ **Note**: If you work from different locations (home, office, café), you'll need to add each IP address, or use "Allow Access from Anywhere" for convenience (less secure).

---

### Step 5: Get Connection String

1. Go to **"Database"** in left sidebar (or click **"Go to Databases"**)
2. Find your cluster (e.g., `Cluster0` or `sedv-demo`)
3. Click **"Connect"** button
4. Choose **"Drivers"**
5. Select:
   - **Driver**: Python
   - **Version**: 3.12 or later
6. Copy the connection string - it looks like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

---

### Step 6: Configure Connection String

1. Open your project's `.env` file
2. Find the line: `SEDV_MONGODB_URI=...`
3. Replace with your connection string, **substituting placeholders**:

**Before** (example from Atlas):
```bash
SEDV_MONGODB_URI=mongodb+srv://...
```

**After** (with your actual credentials):
```bash
SEDV_MONGODB_URI=mongodb+srv://sedv_user:MySecurePass123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
```

**Important replacements**:
- `<username>` → Your database username (e.g., `sedv_user`)
- `<password>` → Your database password (e.g., `MySecurePass123`)
- Keep the `@cluster0.xxxxx.mongodb.net` part exactly as provided

⚠️ **Password encoding**: If your password contains special characters (`@`, `:`, `/`, `?`, `#`, `[`, `]`), you must URL-encode them:
- `@` → `%40`
- `:` → `%3A`
- `/` → `%2F`
- Example: `Pass@123` → `Pass%40123`

---

### Step 7: Verify Connection

Test the connection:

```bash
# From project root
npm run dev:backend
```

Check the backend logs:
- ✅ **Success**: You'll see `"Connected to MongoDB"` or similar
- ❌ **Error**: See troubleshooting below

---

## Troubleshooting

### Error: "Authentication failed"

**Cause**: Wrong username or password in connection string.

**Solution**:
1. Go to **"Database Access"** in Atlas
2. Verify username matches what's in your `.env`
3. If needed, click **"Edit"** on the user and reset password
4. Update `.env` with new password

---

### Error: "Connection timeout" or "Could not connect"

**Cause**: Your IP address is not whitelisted.

**Solution**:
1. Go to **"Network Access"** in Atlas
2. Check if your current IP is listed
3. If not, click **"Add IP Address"** → **"Add Current IP Address"**
4. Wait 1-2 minutes for changes to propagate

---

### Error: "Invalid connection string"

**Cause**: Malformed connection string or special characters in password.

**Solution**:
1. Verify connection string format:
   ```
   mongodb+srv://username:password@cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
2. Check for spaces or line breaks in `.env`
3. URL-encode special characters in password (see Step 6)

---

### Error: "Database does not exist"

**Cause**: Database `sedv` hasn't been created yet.

**Solution**: This is normal! The database will be created automatically when you run the seed script:
```bash
npm run seed
```

---

## Database Structure

After seeding, your Atlas cluster will have:

**Database**: `sedv`

**Collections**:
- `organizations` - Demo organization
- `users` - Admin, manager, and user accounts
- `files` - File metadata (encrypted blobs stored locally)
- `auth_sessions` - JWT session tracking
- `audit_logs` - Security audit trail

You can view these in Atlas:
1. Go to **"Database"** → **"Browse Collections"**
2. Select `sedv` database
3. Explore collections and documents

---

## Security Best Practices

1. **Never commit `.env` to git**
   - `.env` is in `.gitignore` by default
   - Use `.env.example` as template

2. **Use strong passwords**
   - Minimum 12 characters
   - Mix of letters, numbers, symbols
   - Avoid common words

3. **Restrict IP access**
   - Add only your development IPs
   - Avoid `0.0.0.0/0` (allow from anywhere) in production

4. **Rotate credentials regularly**
   - Change database password every 90 days
   - Update `.env` after rotation

5. **Use separate clusters for dev/prod**
   - Free tier for development
   - Paid tier for production with backups

---

## Monitoring and Maintenance

### View Database Metrics

1. Go to **"Database"** in Atlas
2. Click on your cluster name
3. View:
   - **Metrics**: CPU, memory, connections
   - **Real-time**: Current operations
   - **Profiler**: Slow queries

### Backup and Restore

Free tier includes:
- **Automatic snapshots**: Not available on M0
- **Manual export**: Use `mongodump` or Atlas UI

To export data:
1. Go to **"Database"** → **"Browse Collections"**
2. Select collection
3. Click **"Export Collection"** (JSON or CSV)

---

## Upgrading from Free Tier

When you need more:
- **Storage**: M0 has 512 MB limit
- **Performance**: Shared CPU/RAM on M0
- **Backups**: Not available on M0

To upgrade:
1. Go to **"Database"** → Click cluster name
2. Click **"Upgrade"** or **"Edit Configuration"**
3. Choose M2 ($9/month) or higher
4. No data migration needed - seamless upgrade

---

## Additional Resources

- [MongoDB Atlas Documentation](https://www.mongodb.com/docs/atlas/)
- [Connection String Format](https://www.mongodb.com/docs/manual/reference/connection-string/)
- [MongoDB University](https://university.mongodb.com/) - Free courses
- [Atlas Support](https://www.mongodb.com/cloud/atlas/support)

---

## Next Steps

After MongoDB Atlas is set up:
1. ✅ Connection string in `.env`
2. ✅ Backend connects successfully
3. ➡️ Run `npm run seed` to create demo users
4. ➡️ Start development with `npm run dev`

See [development-setup.md](./development-setup.md) for complete workflow.
