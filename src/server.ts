import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import authRoutes from './routes/auth.js';
import projectRoutes from './routes/projects.js';
import catalogRoutes from './routes/catalog.js';
import aiRoutes from './routes/ai.js';
import { errorHandler, notFoundHandler } from './middleware/errorHandler.js';
import sql from './config/db.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// Security middleware
app.use(helmet());
app.use(compression());

// CORS configuration
app.use(
  cors({
    origin: process.env.CORS_ORIGIN || 'http://localhost:5173',
    credentials: true,
  })
);

// Rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000'), // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100'),
  message: 'Too many requests from this IP, please try again later.',
});

app.use('/api/', limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging
if (process.env.NODE_ENV === 'development') {
  app.use(morgan('dev'));
} else {
  app.use(morgan('combined'));
}

// Basic root route for uptime checks
app.get('/', (req, res) => {
  res.json({
    service: 'KABS 2D Design Tool API',
    status: 'ok',
    docs: '/api',
  });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API routes
app.use('/api/auth', authRoutes);
app.use('/api/projects', projectRoutes);
app.use('/api/catalog', catalogRoutes);
app.use('/api/ai', aiRoutes);

// Error handling
app.use(notFoundHandler);
app.use(errorHandler);

// Test database connection on startup
async function testDatabaseConnection() {
  try {
    const result = await sql`SELECT NOW()`;
    console.log('✅ Database connection test successful');
    return true;
  } catch (error: any) {
    console.error('❌ Database connection test failed:');
    if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
      console.error('   Database is not accessible');
      console.error('   Check your DATABASE_URL in .env file');
    } else if (error.code === '28P01') {
      console.error('   Database authentication failed');
      console.error('   Check your DATABASE_URL password in .env file');
    } else if (error.code === '3D000') {
      console.error('   Database does not exist');
    } else {
      console.error('   Error:', error.message);
    }
    console.error('\n💡 Check your DATABASE_URL in backend/.env file\n');
    return false;
  }
}

// Start server
app.listen(PORT, async () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📝 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`🔗 CORS enabled for: ${process.env.CORS_ORIGIN || 'http://localhost:5173'}`);
  console.log('');
  
  // Test database connection
  await testDatabaseConnection();
});

export default app;

