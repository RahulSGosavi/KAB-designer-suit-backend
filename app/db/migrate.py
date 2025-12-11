# app/db/migrate.py
import os
import sys
from dotenv import load_dotenv
from app.config.db import get_db, return_db
import psycopg2

load_dotenv()

def migrate():
    """Add missing columns to existing tables"""
    conn = get_db()
    try:
        cur = conn.cursor()
        
        print("🔄 Running database migrations...")
        
        # Add columns to projects table if they don't exist
        migrations = [
            # Create folders table FIRST (before adding foreign key)
            """
            CREATE TABLE IF NOT EXISTS folders (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                parent_folder_id UUID REFERENCES folders(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Add design_mode column
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'projects' AND column_name = 'design_mode'
                ) THEN
                    ALTER TABLE projects ADD COLUMN design_mode VARCHAR(50) DEFAULT '2d';
                END IF;
            END $$;
            """,
            
            # Add is_draft column
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'projects' AND column_name = 'is_draft'
                ) THEN
                    ALTER TABLE projects ADD COLUMN is_draft BOOLEAN DEFAULT false;
                END IF;
            END $$;
            """,
            
            # Add folder_id column (after folders table exists)
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'projects' AND column_name = 'folder_id'
                ) THEN
                    ALTER TABLE projects ADD COLUMN folder_id UUID REFERENCES folders(id) ON DELETE SET NULL;
                END IF;
            END $$;
            """,
            
            # Create indexes if they don't exist
            """
            CREATE INDEX IF NOT EXISTS idx_projects_design_mode ON projects(design_mode);
            CREATE INDEX IF NOT EXISTS idx_projects_is_draft ON projects(is_draft);
            CREATE INDEX IF NOT EXISTS idx_projects_folder_id ON projects(folder_id);
            CREATE INDEX IF NOT EXISTS idx_folders_company_id ON folders(company_id);
            CREATE INDEX IF NOT EXISTS idx_folders_user_id ON folders(user_id);
            """,
            
            # Create AI suggestions table if it doesn't exist
            """
            CREATE TABLE IF NOT EXISTS ai_suggestions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                issue_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                description TEXT NOT NULL,
                element_ids TEXT[],
                suggestion TEXT NOT NULL,
                fix_action JSONB,
                applied BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Create AI prompts table if it doesn't exist
            """
            CREATE TABLE IF NOT EXISTS ai_prompts (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                prompt TEXT NOT NULL,
                result JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # Create indexes for AI tables
            """
            CREATE INDEX IF NOT EXISTS idx_ai_suggestions_project_id ON ai_suggestions(project_id);
            CREATE INDEX IF NOT EXISTS idx_ai_prompts_project_id ON ai_prompts(project_id);
            """,
        ]
        
        for i, migration in enumerate(migrations, 1):
            try:
                cur.execute(migration)
                print(f"  ✅ Migration {i}/{len(migrations)} completed")
            except psycopg2.Error as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print(f"  ⚠️  Migration {i}/{len(migrations)}: Already applied (skipping)")
                else:
                    print(f"  ❌ Migration {i}/{len(migrations)} failed: {e}")
                    raise
        
        conn.commit()
        print("✅ All migrations completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cur.close()
        return_db(conn)

if __name__ == "__main__":
    migrate()

