# app/routers/projects.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from app.middleware.auth import get_current_user
from app.config.db import execute_query, get_db, return_db
from app.middleware.error_handler import AppError

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    data: Optional[dict[str, Any]] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

@router.get("/")
async def get_projects(current_user: dict = Depends(get_current_user)):
    try:
        company_id = current_user["companyId"]
        
        result = execute_query(
            """
            SELECT p.id, p.name, p.description, p.status, p.design_mode, p.is_draft, p.folder_id, 
                   p.created_at, p.updated_at, u.email as created_by,
                   (SELECT COUNT(*) FROM project_data pd WHERE pd.project_id = p.id) as version_count
            FROM projects p
            JOIN users u ON p.user_id = u.id
            WHERE p.company_id = %s
            ORDER BY p.updated_at DESC
            """,
            (company_id,)
        )
        
        return {"projects": result}
    except Exception as e:
        print(f"Get projects error: {e}")
        raise AppError(str(e), 500)

@router.get("/{project_id}")
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    try:
        company_id = current_user["companyId"]
        
        # Get project
        project_result = execute_query(
            """
            SELECT p.*, u.email as created_by
            FROM projects p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = %s AND p.company_id = %s
            """,
            (project_id, company_id)
        )
        
        if not project_result:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = project_result[0]
        
        # Get latest project data
        data_result = execute_query(
            """
            SELECT data_json, version, updated_at
            FROM project_data
            WHERE project_id = %s
            ORDER BY version DESC
            LIMIT 1
            """,
            (project_id,)
        )
        
        # Get PDF backgrounds
        pdf_result = execute_query(
            """
            SELECT id, file_url, file_name, page_count, metadata, created_at
            FROM pdf_backgrounds
            WHERE project_id = %s
            ORDER BY created_at DESC
            """,
            (project_id,)
        )
        
        return {
            "project": {
                **project,
                "data": data_result[0]["data_json"] if data_result else None,
                "version": data_result[0]["version"] if data_result else 0,
                "pdfBackgrounds": pdf_result,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get project error: {e}")
        raise AppError(str(e), 500)

@router.post("/")
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user["companyId"]
    user_id = current_user["userId"]
    
    # Extract design_mode, is_draft, folder_id from data if provided
    design_mode = project.data.get("design_mode", "2d") if project.data else "2d"
    is_draft = project.data.get("is_draft", True) if project.data else True
    folder_id = project.data.get("folder_id") if project.data else None
    
    # Use a single connection for both operations
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Create project
        cur.execute(
            """
            INSERT INTO projects (company_id, user_id, name, description, design_mode, is_draft, folder_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (company_id, user_id, project.name, project.description, design_mode, is_draft, folder_id)
        )
        
        project_row = cur.fetchone()
        if not project_row:
            raise AppError("Failed to create project - no result returned", 500)
        
        created_project = dict(project_row)
        project_id = created_project["id"]
        
        # Save initial project data if provided (in the same transaction)
        if project.data:
            cur.execute(
                """
                INSERT INTO project_data (project_id, data_json, version)
                VALUES (%s, %s, 1)
                """,
                (project_id, json.dumps(project.data))
            )
        
        # Commit both operations together
        conn.commit()
        cur.close()
        
        return {"project": created_project}
    except psycopg2.IntegrityError as db_error:
        conn.rollback()
        error_msg = str(db_error)
        print(f"Database integrity error creating project: {db_error}")
        if "foreign key constraint" in error_msg.lower():
            raise AppError(f"Foreign key constraint violation: {str(db_error)}", 500)
        raise AppError(f"Database error: {str(db_error)}", 500)
    except Exception as e:
        conn.rollback()
        print(f"Create project error: {e}")
        import traceback
        traceback.print_exc()
        raise AppError(str(e), 500)
    finally:
        return_db(conn)

@router.put("/{project_id}")
async def update_project(project_id: str, project: ProjectUpdate, current_user: dict = Depends(get_current_user)):
    try:
        company_id = current_user["companyId"]
        
        # Check if project exists and belongs to company
        existing = execute_query(
            "SELECT id FROM projects WHERE id = %s AND company_id = %s",
            (project_id, company_id)
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Build update query
        updates = []
        params = []
        
        if project.name is not None:
            updates.append("name = %s")
            params.append(project.name)
        if project.description is not None:
            updates.append("description = %s")
            params.append(project.description)
        
        if not updates:
            # Return existing project
            result = execute_query(
                "SELECT * FROM projects WHERE id = %s",
                (project_id,)
            )
            return {"project": result[0]}
        
        params.append(project_id)
        params.append(company_id)
        
        query = f"""
            UPDATE projects 
            SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND company_id = %s
            RETURNING *
        """
        
        result = execute_query(query, tuple(params))
        
        return {"project": result[0]}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update project error: {e}")
        raise AppError(str(e), 500)

@router.post("/{project_id}/data")
async def save_project_data(project_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    try:
        company_id = current_user["companyId"]
        
        # Verify project belongs to company
        project = execute_query(
            "SELECT id FROM projects WHERE id = %s AND company_id = %s",
            (project_id, company_id)
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get current version
        version_result = execute_query(
            "SELECT COALESCE(MAX(version), 0) as max_version FROM project_data WHERE project_id = %s",
            (project_id,)
        )
        
        next_version = (version_result[0]["max_version"] if version_result else 0) + 1
        
        # Save data
        execute_query(
            """
            INSERT INTO project_data (project_id, data_json, version)
            VALUES (%s, %s, %s)
            """,
            (project_id, json.dumps(data), next_version)
        )
        
        return {"message": "Project data saved", "version": next_version}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Save project data error: {e}")
        raise AppError(str(e), 500)

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    try:
        company_id = current_user["companyId"]
        
        # Verify project belongs to company
        project = execute_query(
            "SELECT id FROM projects WHERE id = %s AND company_id = %s",
            (project_id, company_id)
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete project (cascade will delete related data)
        execute_query(
            "DELETE FROM projects WHERE id = %s AND company_id = %s",
            (project_id, company_id)
        )
        
        return {"message": "Project deleted"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete project error: {e}")
        raise AppError(str(e), 500)

