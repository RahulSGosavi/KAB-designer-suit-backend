import postgres from 'postgres';
import dotenv from 'dotenv';

dotenv.config();

// Use Supabase connection string from .env
const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  console.error('❌ DATABASE_URL is not set in .env file');
  console.error('   Please create backend/.env file with:');
  console.error('   DATABASE_URL=postgresql://postgres:oUYxwmuAv66U9bw7@db.ehbrtcvtelsvsphvairj.supabase.co:5432/postgres');
}

const sql = postgres(connectionString || '', {
  max: 20,
  idle_timeout: 30,
  connect_timeout: 10,
});

export default sql;

