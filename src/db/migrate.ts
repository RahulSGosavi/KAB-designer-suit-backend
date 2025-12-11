import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import sql from '../config/db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function migrate() {
  try {
    console.log('🔄 Running database migrations...');

    if (!process.env.DATABASE_URL) {
      console.error('❌ DATABASE_URL is not set in .env file');
      console.error('   Please create backend/.env file with your Supabase connection string');
      process.exit(1);
    }

    const schemaPath = path.join(__dirname, 'schema.sql');
    const schema = fs.readFileSync(schemaPath, 'utf-8');

    // Execute the entire schema
    await sql.unsafe(schema);

    console.log('✅ Database migrations completed successfully');
    await sql.end();
    process.exit(0);
  } catch (error: any) {
    console.error('❌ Migration failed:', error.message);
    if (error.code === 'ECONNREFUSED') {
      console.error('   Cannot connect to database. Check your DATABASE_URL in .env file');
    } else if (error.message?.includes('already exists') || error.code === '42P07') {
      console.log('   Some tables already exist (this is OK)');
      console.log('✅ Database migrations completed');
    } else {
      console.error('   Error details:', error);
    }
    await sql.end();
    process.exit(1);
  }
}

migrate();
