# models.py - Database models

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    mobile_number = Column(String, nullable=True)
    
    # Birth details - Nullable for OAuth users initially
    date_of_birth = Column(String, nullable=True)  # YYYY-MM-DD
    time_of_birth = Column(String, nullable=True)  # HH:MM
    location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String, default="Asia/Kolkata", nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class ChartData(Base):
    __tablename__ = "chart_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Store computed chart data as JSON (or we can normalize this later)
    # For now, storing the key birth parameters that are needed to recompute
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    hour = Column(Integer, nullable=False)
    minute = Column(Integer, default=0)
    second = Column(Integer, default=0)
    tz = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    
    # Store computed chart result (JSON string or use JSONB if PostgreSQL supports it)
    # For simplicity, we'll recompute on demand, but we could cache results here
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())



class FamilyMember(Base):
    __tablename__ = "user_family_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)  # ForeignKey logic manually or implicit
    name = Column(String, nullable=False)
    relationship = Column(String, nullable=True)  # e.g., "Father", "Spouse"
    gender = Column(String, nullable=True)  # "Male", "Female", "Other"
    
    date_of_birth = Column(String, nullable=False)  # YYYY-MM-DD
    time_of_birth = Column(String, nullable=False)  # HH:MM
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String, default="Asia/Kolkata", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
