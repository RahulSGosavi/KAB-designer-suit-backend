import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Pool } = pg;

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'kab_design_tool',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Test connection
pool.on('connect', () => {
  console.log('✅ Database connected successfully');
});

pool.on('error', (err: NodeJS.ErrnoException) => {
  console.error('❌ Database connection error:', err);
  if (err.code === 'ECONNREFUSED') {
    console.error('💡 PostgreSQL is not running or not accessible');
    console.error('   Please ensure PostgreSQL is installed and running');
    console.error('   Check your .env file for correct database credentials');
  }
  // Don't exit in production, let the app handle it gracefully
  if (process.env.NODE_ENV === 'development') {
    // process.exit(-1);
  }
});

export default pool;

