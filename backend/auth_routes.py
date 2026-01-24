# auth_routes.py - Authentication API endpoints

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
from backend.database import get_db
from backend.models import User, ChartData
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from backend.auth import (
    authenticate_user,
    get_password_hash,
    create_access_token,
    get_user_by_email,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Request Models
class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    mobile_number: str
    date_of_birth: str  # YYYY-MM-DD
    time_of_birth: str  # HH:MM
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = "Asia/Kolkata"


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    token: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    mobile_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    time_of_birth: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = "Asia/Kolkata"

    class Config:
        from_attributes = True


# Helper to get current user from token
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    from jose import JWTError, jwt
    from backend.auth import SECRET_KEY, ALGORITHM
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    """Create a new user account."""
    try:
        # Validate password length
        if len(request.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        
        # Check if user already exists
        existing_user = get_user_by_email(db, email=request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(request.password)
        new_user = User(
            email=request.email,
            name=request.name,
            password_hash=hashed_password,
            mobile_number=request.mobile_number,
            date_of_birth=request.date_of_birth,
            time_of_birth=request.time_of_birth,
            location=request.location,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": new_user.email}, expires_delta=access_token_expires
        )
        
        # Create chart data entry for this user
        # Parse birth date to extract year, month, day, hour, minute
        dob_parts = request.date_of_birth.split("-")
        time_parts = request.time_of_birth.split(":")
        
        chart_data = ChartData(
            user_id=new_user.id,
            year=int(dob_parts[0]),
            month=int(dob_parts[1]),
            day=int(dob_parts[2]),
            hour=int(time_parts[0]),
            minute=int(time_parts[1]) if len(time_parts) > 1 else 0,
            tz=request.timezone,
            lat=request.latitude or 0.0,
            lon=request.longitude or 0.0
        )
        db.add(chart_data)
        db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "name": new_user.name,
                "mobile_number": new_user.mobile_number,
                "date_of_birth": new_user.date_of_birth,
                "time_of_birth": new_user.time_of_birth,
                "location": new_user.location,
                "latitude": new_user.latitude,
                "longitude": new_user.longitude,
                "timezone": new_user.timezone
            }
        }
    except HTTPException:
        # Re-raise HTTP exceptions (they already have proper status codes)
        raise
    except Exception as e:
        # Rollback on error
        db.rollback()
        # Log the error for debugging
        import traceback
        print(f"Signup error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/login", response_model=Token)
def login(request: SignInRequest, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    user = authenticate_user(db, email=request.email, password=request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "mobile_number": user.mobile_number,
            "date_of_birth": user.date_of_birth,
            "time_of_birth": user.time_of_birth,
            "location": user.location,
            "latitude": user.latitude,
            "longitude": user.longitude,
            "timezone": user.timezone
        }
    }


@router.post("/google", response_model=Token)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with Google OAuth."""
    try:
        # Verify the token
        # Get Client ID from env or use a placeholder that the user must replace
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
        
        id_info = id_token.verify_oauth2_token(
            request.token, requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=10
        )

        email = id_info.get("email")
        name = id_info.get("name")
        
        if not email:
            raise HTTPException(status_code=400, detail="Invalid Google Token: No email found")

        # Check if user exists
        user = get_user_by_email(db, email=email)
        
        if not user:
            # Create new user
            # We don't have password or birth details yet
            user = User(
                email=email,
                name=name,
                password_hash=None, # No password for Google users initially
                mobile_number=None,
                date_of_birth=None,
                time_of_birth=None,
                location=None,
                latitude=None,
                longitude=None
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "mobile_number": user.mobile_number,
                "date_of_birth": user.date_of_birth,
                "time_of_birth": user.time_of_birth,
                "location": user.location,
                "latitude": user.latitude,
                "longitude": user.longitude,
                "timezone": user.timezone
            }
        }
        
    except ValueError as e:
        # Invalid token
        raise HTTPException(status_code=400, detail=f"Invalid Google Token: {str(e)}")
    except Exception as e:
        import traceback
        print(f"Google Login error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    time_of_birth: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None


@router.put("/me", response_model=UserResponse)
def update_user_profile(
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile and birth chart data."""
    try:
        # Update user fields if provided
        if request.name is not None:
            current_user.name = request.name
        if request.email is not None:
            # Check if email is taken by another user
            if request.email != current_user.email:
                existing = get_user_by_email(db, request.email)
                if existing:
                    raise HTTPException(status_code=400, detail="Email already in use")
            current_user.email = request.email
        if request.mobile_number is not None:
            current_user.mobile_number = request.mobile_number
        if request.date_of_birth is not None:
            current_user.date_of_birth = request.date_of_birth
        if request.time_of_birth is not None:
            current_user.time_of_birth = request.time_of_birth
        if request.location is not None:
            current_user.location = request.location
        if request.latitude is not None:
            current_user.latitude = request.latitude
        if request.longitude is not None:
            current_user.longitude = request.longitude
        if request.timezone is not None:
            current_user.timezone = request.timezone
            
        db.commit()
        db.refresh(current_user)
        
        # If birth details changed, update ChartData
        # For simplicity, we create a new ChartData entry or update the latest one
        # Let's check if we should update chart data
        birth_fields_changed = any([
            request.date_of_birth, request.time_of_birth, 
            request.latitude, request.longitude, request.timezone
        ])
        
        if birth_fields_changed:
            # Parse new values (falling back to current user values if not in request)
            dob = request.date_of_birth or current_user.date_of_birth
            tob = request.time_of_birth or current_user.time_of_birth
            lat = request.latitude if request.latitude is not None else current_user.latitude
            lon = request.longitude if request.longitude is not None else current_user.longitude
            tz = request.timezone or current_user.timezone
            
            if not dob or not tob:
                # Can't create chart data without full birth details
                # If we are here, it means we are updating partial data, but still missing core fields
                # So we just skip chart update or raise error? 
                # Let's skip chart update if data is incomplete
                pass
            else:
                dob_parts = dob.split("-")
                time_parts = tob.split(":")
            
            # Find existing latest chart data
            chart_data = db.query(ChartData).filter(
                ChartData.user_id == current_user.id
            ).order_by(ChartData.created_at.desc()).first()
            
            if chart_data:
                chart_data.year = int(dob_parts[0])
                chart_data.month = int(dob_parts[1])
                chart_data.day = int(dob_parts[2])
                chart_data.hour = int(time_parts[0])
                chart_data.minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                chart_data.lat = lat
                chart_data.lon = lon
                chart_data.tz = tz
            else:
                # Create new if somehow missing
                chart_data = ChartData(
                    user_id=current_user.id,
                    year=int(dob_parts[0]),
                    month=int(dob_parts[1]),
                    day=int(dob_parts[2]),
                    hour=int(time_parts[0]),
                    minute=int(time_parts[1]) if len(time_parts) > 1 else 0,
                    lat=lat,
                    lon=lon,
                    tz=tz
                )
                db.add(chart_data)
            
            db.commit()

        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.get("/chart-data")
def get_user_chart_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's birth data for chart computation."""
    chart_data = db.query(ChartData).filter(
        ChartData.user_id == current_user.id
    ).order_by(ChartData.created_at.desc()).first()
    
    if not chart_data:
        # Return user's birth details from user table
        if not current_user.date_of_birth or not current_user.time_of_birth:
             return None # Or raise 404, frontend should handle "profile incomplete"

        dob_parts = current_user.date_of_birth.split("-")
        time_parts = current_user.time_of_birth.split(":")
        return {
            "year": int(dob_parts[0]),
            "month": int(dob_parts[1]),
            "day": int(dob_parts[2]),
            "hour": int(time_parts[0]),
            "minute": int(time_parts[1]) if len(time_parts) > 1 else 0,
            "second": 0,
            "tz": current_user.timezone,
            "lat": current_user.latitude or 0.0,
            "lon": current_user.longitude or 0.0
        }
    
    return {
        "year": chart_data.year,
        "month": chart_data.month,
        "day": chart_data.day,
        "hour": chart_data.hour,
        "minute": chart_data.minute,
        "second": chart_data.second,
        "tz": chart_data.tz,
        "lat": chart_data.lat,
        "lon": chart_data.lon
    }

