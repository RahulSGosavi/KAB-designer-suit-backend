# app/config/db.py
import os
import psycopg2
from psycopg2 import pool, extras
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL is not set in .env file")
    print("   Please create backend/.env file with:")
    print("   DATABASE_URL=postgresql://user:password@host:port/database")

# Connection pool
connection_pool = None

def get_connection_pool():
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20, DATABASE_URL
            )
        except Exception as e:
            print(f"❌ Failed to create connection pool: {e}")
            raise
    return connection_pool

def get_db():
    """Get database connection from pool"""
    pool = get_connection_pool()
    return pool.getconn()

def return_db(conn):
    """Return connection to pool"""
    pool = get_connection_pool()
    pool.putconn(conn)

def execute_query(query, params=None, commit=True):
    """Execute a query and return results"""
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if cur.description:
                results = cur.fetchall()
                # Convert to list of dicts
                return [dict(row) for row in results]
            if commit:
                conn.commit()
            return []
    except Exception as e:
        conn.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        if commit:
            return_db(conn)

def execute_in_transaction(queries):
    """Execute multiple queries in a single transaction"""
    conn = get_db()
    results = []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for query, params in queries:
                cur.execute(query, params)
                if cur.description:
                    results.append([dict(row) for row in cur.fetchall()])
                else:
                    results.append([])
        conn.commit()
        return results
    except Exception as e:
        conn.rollback()
        print(f"Transaction error: {e}")
        raise
    finally:
        return_db(conn)

def get_db_connection():
    """Get a database connection that can be used for multiple operations"""
    return get_db()

def commit_and_close(conn):
    """Commit and return connection to pool"""
    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        return_db(conn)

