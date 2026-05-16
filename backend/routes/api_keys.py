from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import secrets
import hashlib

from backend.database import get_db
from backend.models import User, APIKey
from backend.dependencies import get_current_user_optional

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

class APIKeyCreate(BaseModel):
    name: str

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    created_at: str
    last_used: str | None = None

class APIKeyCreateResponse(APIKeyResponse):
    key: str # Only returned once

@router.post("", response_model=APIKeyCreateResponse)
def create_api_key(
    req: APIKeyCreate,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
    # Generate a secure random API key
    raw_key = f"sk_live_{secrets.token_urlsafe(32)}"
    
    # Hash it
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    # Keep track of first few characters
    prefix = raw_key[:12] + "..."
    
    db_api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        name=req.name,
        key_prefix=prefix
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return {
        "id": db_api_key.id,
        "name": db_api_key.name,
        "key_prefix": db_api_key.key_prefix,
        "is_active": db_api_key.is_active,
        "created_at": str(db_api_key.created_at),
        "last_used": str(db_api_key.last_used) if db_api_key.last_used else None,
        "key": raw_key # The only time we'll ever show this to the user!
    }

@router.get("", response_model=List[APIKeyResponse])
def get_api_keys(
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
    keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    
    return [
        {
            "id": k.id,
            "name": k.name,
            "key_prefix": k.key_prefix,
            "is_active": k.is_active,
            "created_at": str(k.created_at),
            "last_used": str(k.last_used) if k.last_used else None
        } for k in keys
    ]

@router.delete("/{key_id}")
def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        
    db_api_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == current_user.id).first()
    
    if not db_api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    db.delete(db_api_key)
    db.commit()
    
    return {"status": "success", "message": "API key deleted"}
