# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import re
import psycopg2
import hashlib
from psycopg2.extras import RealDictCursor
from app.config.db import execute_query, get_db, return_db
from app.middleware.error_handler import AppError

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def prepare_password_for_bcrypt(password: str) -> str:
    """
    Pre-hash password with SHA-256 to allow passwords longer than bcrypt's 72-byte limit.
    This is a common pattern that maintains security while removing length restrictions.
    """
    # Hash with SHA-256 (always 64 bytes, well under bcrypt's 72-byte limit)
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256(password_bytes).hexdigest()
    return sha256_hash

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_EXPIRES_IN = os.getenv("JWT_EXPIRES_IN", "7d")

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    companyName: str
    firstName: str | None = None
    lastName: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def create_company_slug(name: str) -> str:
    """Create URL-friendly slug from company name"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug

def get_unique_company_slug(base_slug: str) -> str:
    """Get a unique company slug, appending number if needed"""
    from app.config.db import execute_query
    
    slug = base_slug
    counter = 1
    
    while True:
        existing = execute_query(
            "SELECT id FROM companies WHERE slug = %s",
            (slug,)
        )
        
        if not existing:
            return slug
        
        # Slug exists, try with number suffix
        slug = f"{base_slug}-{counter}"
        counter += 1
        
        # Safety limit
        if counter > 1000:
            # Use timestamp as fallback
            import time
            slug = f"{base_slug}-{int(time.time())}"
            break
    
    return slug

def get_jwt_expires_in() -> timedelta:
    """Parse JWT_EXPIRES_IN string to timedelta"""
    expires_in = JWT_EXPIRES_IN.lower()
    if expires_in.endswith('d'):
        days = int(expires_in[:-1])
        return timedelta(days=days)
    elif expires_in.endswith('h'):
        hours = int(expires_in[:-1])
        return timedelta(hours=hours)
    elif expires_in.endswith('m'):
        minutes = int(expires_in[:-1])
        return timedelta(minutes=minutes)
    else:
        return timedelta(days=7)  # Default 7 days

def create_token(user_id: str, company_id: str, role: str) -> str:
    """Create JWT token"""
    expires_delta = get_jwt_expires_in()
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "userId": user_id,
        "companyId": company_id,
        "role": role,
        "exp": expire
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@router.post("/register")
async def register(request: RegisterRequest):
    try:
        # Validate password
        if len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Check if user already exists
        existing_user = execute_query(
            "SELECT id FROM users WHERE email = %s",
            (request.email,)
        )
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create company with unique slug
        base_slug = create_company_slug(request.companyName)
        company_slug = get_unique_company_slug(base_slug)
        
        # Hash password: pre-hash with SHA-256 to support any length, then bcrypt
        # This allows passwords longer than bcrypt's 72-byte limit
        prepared_password = prepare_password_for_bcrypt(request.password)
        password_hash = pwd_context.hash(prepared_password)
        
        # Use a single connection for both operations to ensure consistency
        conn = get_db()
        company = None
        user = None
        company_id = None
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Create company
            try:
                cur.execute(
                    """
                    INSERT INTO companies (name, slug) 
                    VALUES (%s, %s)
                    RETURNING id, name, slug
                    """,
                    (request.companyName, company_slug)
                )
                company_row = cur.fetchone()
            except psycopg2.IntegrityError as db_error:
                error_msg = str(db_error)
                # Handle duplicate slug constraint violation
                if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower() or "companies_slug_key" in error_msg.lower():
                    # Try again with a new unique slug
                    company_slug = get_unique_company_slug(base_slug)
                    cur.execute(
                        """
                        INSERT INTO companies (name, slug) 
                        VALUES (%s, %s)
                        RETURNING id, name, slug
                        """,
                        (request.companyName, company_slug)
                    )
                    company_row = cur.fetchone()
                else:
                    raise
            
            if not company_row:
                raise AppError("Failed to create company - no result returned", 500)
            
            company = dict(company_row)
            company_id = company["id"]  # Keep as UUID object from PostgreSQL
            
            if not company_id:
                raise AppError("Company ID is invalid", 500)
            
            # Now create user in the same transaction using the company_id
            cur.execute(
                """
                INSERT INTO users (company_id, email, password_hash, first_name, last_name, role) 
                VALUES (%s, %s, %s, %s, %s, 'admin')
                RETURNING id, email, first_name, last_name, role
                """,
                (company_id, request.email, password_hash, request.firstName, request.lastName)
            )
            user_row = cur.fetchone()
            
            if not user_row:
                raise AppError("Failed to create user - no result returned", 500)
            
            user = dict(user_row)
            
            # Commit both operations together
            conn.commit()
            cur.close()
            
        except psycopg2.IntegrityError as db_error:
            conn.rollback()
            error_msg = str(db_error)
            print(f"Database integrity error: {db_error}")
            if "foreign key constraint" in error_msg.lower() or "users_company_id_fkey" in error_msg.lower():
                company_id_str = str(company_id) if company_id else "unknown"
                raise AppError(f"Foreign key constraint violation. Company ID: {company_id_str}. Error: {str(db_error)}", 500)
            elif "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
                raise AppError("A record with this information already exists", 400)
            raise AppError(f"Database error: {str(db_error)}", 500)
        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            import traceback
            traceback.print_exc()
            raise AppError(f"Registration failed: {str(e)}", 500)
        finally:
            return_db(conn)
        
        # Generate token (convert UUIDs to strings for JWT)
        token = create_token(
            str(user["id"]), 
            str(company_id), 
            user["role"]
        )
        
        return {
            "token": token,
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "firstName": user["first_name"],
                "lastName": user["last_name"],
                "role": user["role"],
            },
            "company": {
                "id": str(company_id),
                "name": company["name"],
                "slug": company["slug"],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise AppError(str(e), 500)

@router.post("/login")
async def login(request: LoginRequest):
    try:
        # Find user with company
        result = execute_query(
            """
            SELECT u.id, u.email, u.password_hash, u.first_name, u.last_name, u.role, u.company_id,
                   c.id as company_id, c.name as company_name, c.slug as company_slug
            FROM users u
            JOIN companies c ON u.company_id = c.id
            WHERE u.email = %s AND u.status = 'active'
            """,
            (request.email,)
        )
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = result[0]
        
        # Verify password: try new method (SHA-256 + bcrypt) first, then fallback to old method (direct bcrypt)
        # This ensures backward compatibility with existing users
        prepared_password = prepare_password_for_bcrypt(request.password)
        password_valid = pwd_context.verify(prepared_password, user["password_hash"])
        
        # If new method fails, try old method for backward compatibility
        if not password_valid:
            password_valid = pwd_context.verify(request.password, user["password_hash"])
        
        if not password_valid:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate token
        token = create_token(str(user["id"]), str(user["company_id"]), user["role"])
        
        return {
            "token": token,
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "firstName": user["first_name"],
                "lastName": user["last_name"],
                "role": user["role"],
            },
            "company": {
                "id": str(user["company_id"]),
                "name": user["company_name"],
                "slug": user["company_slug"],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise AppError(str(e), 500)

