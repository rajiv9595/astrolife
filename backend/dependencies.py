from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.api_key import APIKeyHeader
from typing import Optional, Any
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.auth import SECRET_KEY, ALGORITHM
from backend.database import get_db
from backend.models import User
from backend.auth_routes import get_user_by_email

# OAuth2 scheme for optional authentication (auto_error=False)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if token or API key is provided, otherwise return None."""
    # First check API key
    if api_key:
        import hashlib
        from backend.models import APIKey
        from datetime import datetime
        import pytz
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        db_key = db.query(APIKey).filter(APIKey.key_hash == key_hash, APIKey.is_active == True).first()
        if db_key:
            user = db.query(User).filter(User.id == db_key.user_id, User.is_active == True).first()
            if user:
                # Update last used
                db_key.last_used = datetime.now(pytz.utc)
                db.commit()
                return user
        
    # Then check token
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email:
            user = get_user_by_email(db, email=email)
            return user
    except JWTError:
        pass
    except Exception:
        pass
    
    return None
