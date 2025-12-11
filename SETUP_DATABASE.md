# Database Setup Guide

## Quick Setup (Windows)

### Step 1: Install PostgreSQL

1. Download from: https://www.postgresql.org/download/windows/
2. Run the installer
3. **Remember the password you set for the `postgres` user**
4. Complete the installation

### Step 2: Start PostgreSQL Service

**Option A: Using Services**
- Press `Win + R`, type `services.msc`
- Find "postgresql-x64-XX" (where XX is version number)
- Right-click → Start

**Option B: Using PowerShell (as Administrator)**
```powershell
Get-Service -Name postgresql* | Start-Service
```

### Step 3: Create Database

Open PowerShell or Command Prompt:

```bash
# Connect to PostgreSQL (use the password you set during installation)
psql -U postgres

# If it asks for password, enter the one you set during installation
# Then run:
CREATE DATABASE kab_design_tool;

# Verify it was created:
\l

# Exit:
\q
```

### Step 4: Create .env File

In the `backend` folder, create a file named `.env`:

```env
PORT=3001
NODE_ENV=development

DB_HOST=localhost
DB_PORT=5432
DB_NAME=kab_design_tool
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD_HERE

JWT_SECRET=kab-design-tool-super-secret-jwt-key-change-in-production-min-32-chars
JWT_EXPIRES_IN=7d

CORS_ORIGIN=http://localhost:5173

RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

**Important:** Replace `YOUR_POSTGRES_PASSWORD_HERE` with the actual password you set during PostgreSQL installation.

### Step 5: Run Migrations

```bash
cd backend
npm run migrate
```

You should see:
```
🔄 Running database migrations...
✅ Database migrations completed successfully
```

### Step 6: Start Backend

```bash
npm run dev
```

You should see:
```
🚀 Server running on port 3001
✅ Database connected successfully
```

## Troubleshooting

### "password authentication failed"
- Check your PostgreSQL password in `.env` file
- Default password is often `postgres` or what you set during installation
- Try: `psql -U postgres` to test password

### "database does not exist"
- Create it: `CREATE DATABASE kab_design_tool;`
- Or use psql: `psql -U postgres -c "CREATE DATABASE kab_design_tool;"`

### "relation does not exist"
- Run migrations: `npm run migrate`
- Check if tables exist: `psql -U postgres -d kab_design_tool -c "\dt"`

### PostgreSQL not starting
- Check if port 5432 is in use
- Check Windows Event Viewer for PostgreSQL errors
- Reinstall PostgreSQL if needed

## Test Database Connection

```bash
# Test connection
psql -U postgres -d kab_design_tool

# If this works, your database is accessible
# Exit with: \q
```

## Alternative: Use SQLite (Simpler, but not recommended for production)

If PostgreSQL is too complex, you can modify the backend to use SQLite, but PostgreSQL is recommended for production use.

