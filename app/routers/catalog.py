# app/routers/catalog.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Any, List
from app.middleware.auth import get_current_user

router = APIRouter()

class BlockDefinition(BaseModel):
    id: str
    name: str
    type: str = "furniture"
    category: str
    manufacturer: Optional[str] = None
    sku: Optional[str] = None
    tags: Optional[List[str]] = None
    moduleClass: Optional[str] = None
    width: float
    height: float
    depth: Optional[float] = None
    description: Optional[str] = None
    planSymbols: Optional[List[Any]] = None

# In-memory catalog (can be replaced with database)
runtime_catalog: List[BlockDefinition] = []

@router.get("/blocks")
async def get_blocks(current_user: dict = Depends(get_current_user)):
    """Get all catalog blocks"""
    return {"blocks": runtime_catalog}

@router.post("/blocks")
async def create_block(block: BlockDefinition, current_user: dict = Depends(get_current_user)):
    """Create or update a catalog block"""
    global runtime_catalog
    
    # Remove existing block with same id
    runtime_catalog = [b for b in runtime_catalog if b.id != block.id]
    
    # Add new block
    runtime_catalog.append(block)
    
    return {"block": block}

