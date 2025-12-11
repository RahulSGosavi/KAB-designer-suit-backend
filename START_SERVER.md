# How to Start the FastAPI Backend Server

## Quick Start

### Option 1: Using uvicorn directly (Recommended)
```bash
cd backend
uvicorn main:app --reload --port 3001
```

### Option 2: Using the run script
```bash
cd backend
python run.py
```

### Option 3: Using Python directly
```bash
cd backend
python main.py
```

## Verify Server is Running

After starting, you should see:
```
🚀 Starting KABS Design Tool API on http://0.0.0.0:3001
INFO:     Uvicorn running on http://127.0.0.1:3001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Test the Server

Open in browser:
- **API Root**: http://localhost:3001/
- **Health Check**: http://localhost:3001/health
- **API Docs**: http://localhost:3001/docs (Swagger UI)

Or test with curl:
```bash
curl http://localhost:3001/health
```

## Troubleshooting

### Error: "Could not import module 'main'"
- Make sure you're in the `backend` directory
- Check that `main.py` exists

### Error: "Port 3001 already in use"
- Stop any other process using port 3001
- Or change PORT in `.env` file to a different port

### Error: "DATABASE_URL is not set"
- Make sure `.env` file exists in `backend/` directory
- Check that DATABASE_URL is set in `.env`

### Connection Refused Error
- Make sure the server is actually running
- Check that port 3001 is not blocked by firewall
- Verify the server started successfully (check for errors in terminal)

