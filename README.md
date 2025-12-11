# KABS 2D Design Tool - Backend API

Production-ready backend API for the KABS 2D Design Tool with multi-tenant support.

## Features

- ✅ JWT Authentication
- ✅ Multi-tenant architecture (company-based isolation)
- ✅ Project CRUD operations
- ✅ Version history for project data
- ✅ PDF background storage
- ✅ Rate limiting
- ✅ Security middleware (Helmet, CORS)
- ✅ Error handling
- ✅ Input validation

## Quick Start

```bash
# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
npm run migrate

# Start development server
npm run dev

# Build for production
npm run build
npm start
```

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new company and user
- `POST /api/auth/login` - Login user

### Projects

- `GET /api/projects` - List all projects (requires auth)
- `GET /api/projects/:id` - Get project with data (requires auth)
- `POST /api/projects` - Create new project (requires auth)
- `PUT /api/projects/:id` - Update project (requires auth)
- `POST /api/projects/:id/data` - Save project data (requires auth)
- `DELETE /api/projects/:id` - Delete project (requires auth)

## Database Schema

See `src/db/schema.sql` for complete schema.

Key tables:
- `companies` - Tenant/company information
- `users` - User accounts with company association
- `projects` - Project metadata
- `project_data` - Versioned project data (JSONB)
- `pdf_backgrounds` - PDF file references

## Security

- JWT token authentication
- Company-based data isolation
- Password hashing with bcrypt
- Rate limiting
- Input validation
- SQL injection prevention (parameterized queries)

## Environment Variables

See `.env.example` for all required variables.

## Development

```bash
# Watch mode
npm run dev

# Run migrations
npm run migrate

# Type checking
npx tsc --noEmit
```

## Production

```bash
# Build
npm run build

# Start
npm start

# With PM2
pm2 start dist/server.js --name kab-backend
```

