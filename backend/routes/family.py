from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import User, FamilyMember
from backend.schemas import FamilyMemberCreate, FamilyMemberResponse
from backend.auth_routes import get_current_user

router = APIRouter(prefix="/family", tags=["Family Members"])

@router.post("/", response_model=FamilyMemberResponse)
def add_family_member(
    member: FamilyMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new family member."""
    new_member = FamilyMember(
        user_id=current_user.id,
        **member.dict()
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

@router.get("/", response_model=List[FamilyMemberResponse])
def get_family_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all family members for current user."""
    return db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).all()

@router.delete("/{member_id}")
def delete_family_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a family member."""
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    db.delete(member)
    db.commit()
    return {"message": "Member deleted successfully"}

@router.put("/{member_id}", response_model=FamilyMemberResponse)
def update_family_member(
    member_id: int,
    data: FamilyMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a family member."""
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    for key, value in data.dict().items():
        setattr(member, key, value)
        
    db.commit()
    db.refresh(member)
    return member
