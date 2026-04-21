from datetime import datetime, timedelta
import random
import string
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

security = HTTPBearer()

ALGORITHM = "HS256"

# Default secret if not in config
SECRET_KEY = "super-secret-key-12345"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "JWT_EXPIRE_MINUTES", 60 * 24 * 7) # 1 week

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
def decode_token(token: str):
    try:
        # PyJWT handles the 'exp' validation automatically
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("DEBUG: Token has expired")
        return None
    except jwt.PyJWTError as e:
        print(f"DEBUG: JWT Decode Error: {e}")
        return None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=403, 
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=403, 
            detail="Token payload missing 'sub'"
        )

    # CRITICAL: We cast the ID to string to match the JWT payload format
    # and ensure SQLAlchemy can resolve the query against the UUID column
    user = db.query(User).filter(User.id == str(user_id)).first()
    
    if user is None:
        print(f"DEBUG: Payload sub '{user_id}' not found in Database.")
        raise HTTPException(
            status_code=403, 
            detail="User not found"
        )
        
    return user