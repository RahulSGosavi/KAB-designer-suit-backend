# Supabase Database Setup

## Step 1: Create .env File

Create a file named `.env` in the `backend/` folder with the following content:

```env
# Server Configuration
PORT=3001
NODE_ENV=development

# Supabase Database Configuration
DATABASE_URL=postgresql://postgres:oUYxwmuAv66U9bw7@db.ehbrtcvtelsvsphvairj.supabase.co:5432/postgres

# JWT Configuration
JWT_SECRET=kab-design-tool-super-secret-jwt-key-change-in-production-min-32-chars
JWT_EXPIRES_IN=7d

# CORS Configuration
CORS_ORIGIN=http://localhost:5173

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

## Step 2: Run Migrations

```bash
cd backend
npm run migrate
```

This will create all the necessary tables in your Supabase database.

## Step 3: Start Backend Server

```bash
npm run dev
```

You should see:
```
🚀 Server running on port 3001
✅ Database connection test successful
```

## Step 4: Test Registration

The registration endpoint should now work at:
```
POST http://localhost:3001/api/auth/register
```

## Troubleshooting

### "DATABASE_URL is not set"
- Make sure `.env` file exists in `backend/` folder
- Check the file name is exactly `.env` (not `.env.txt`)

### "Connection refused"
- Verify the Supabase connection string is correct
- Check if Supabase database is accessible
- Verify the password in the connection string

### "Tables already exist"
- This is OK if you've run migrations before
- The migration will skip creating existing tables

## Connection String Format

```
postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

Your Supabase connection string:
```
postgresql://postgres:oUYxwmuAv66U9bw7@db.ehbrtcvtelsvsphvairj.supabase.co:5432/postgres
```

