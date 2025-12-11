# FastAPI Backend - Running with Uvicorn

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=postgresql://user:password@host:port/database
JWT_SECRET=your-secret-key-min-32-characters
JWT_EXPIRES_IN=7d
CORS_ORIGIN=http://localhost:5173
PORT=8000
NODE_ENV=development
```

### 3. Run with Uvicorn

**Development mode (with auto-reload):**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Production mode:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Alternative: Run directly from Python:**
```bash
cd backend
python main.py
```

## API Endpoints

- **Root**: `http://localhost:8000/`
- **Health Check**: `http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc`

### Authentication
- `POST /api/auth/register` - Register new company and user
- `POST /api/auth/login` - Login user

### Projects
- `GET /api/projects` - List all projects (requires auth)
- `GET /api/projects/{id}` - Get project (requires auth)
- `POST /api/projects` - Create project (requires auth)
- `PUT /api/projects/{id}` - Update project (requires auth)
- `POST /api/projects/{id}/data` - Save project data (requires auth)
- `DELETE /api/projects/{id}` - Delete project (requires auth)

### Catalog
- `GET /api/catalog/blocks` - Get catalog blocks (requires auth)
- `POST /api/catalog/blocks` - Create catalog block (requires auth)

## Testing

Test the API:
```bash
# Health check
curl http://localhost:8000/health

# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","companyName":"Test Company"}'
```

## Troubleshooting

### Error: "Could not import module 'main'"
- Make sure you're in the `backend` directory
- Check that `main.py` exists in the `backend` directory

### Error: "DATABASE_URL is not set"
- Create a `.env` file in the `backend` directory
- Add your database connection string

### Error: Database connection failed
- Verify your `DATABASE_URL` is correct
- Make sure PostgreSQL is running
- Check firewall settings

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── app/
│   ├── routers/           # API routes
│   │   ├── auth.py
│   │   ├── projects.py
│   │   └── catalog.py
│   ├── middleware/        # Middleware
│   │   ├── auth.py
│   │   └── error_handler.py
│   └── config/            # Configuration
│       └── db.py
└── .env                   # Environment variables (create this)
```

