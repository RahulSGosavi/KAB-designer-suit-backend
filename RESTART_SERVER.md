# Restart the FastAPI Server

The server code has been updated. Please restart it to apply the changes.

## Restart Command

```bash
cd backend
uvicorn main:app --reload --port 3001
```

## What Was Fixed

1. **Single Transaction**: Company and user are now created in the same database transaction
2. **Proper UUID Handling**: UUIDs are handled correctly from PostgreSQL
3. **Better Error Handling**: Improved error messages and transaction rollback

## Verify Server is Running

After restarting, test the health endpoint:
```bash
curl http://localhost:3001/health
```

You should see:
```json
{"status":"ok","timestamp":"..."}
```

## Test Registration

The registration should now work without foreign key constraint errors.

