from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
import hashlib
import secrets

# Tentar usar bcrypt, se falhar usar hashlib
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    USE_BCRYPT = True
except Exception:
    USE_BCRYPT = False

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if USE_BCRYPT:
        return pwd_context.verify(plain_password, hashed_password)
    else:
        # Fallback simples com hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    if USE_BCRYPT:
        return pwd_context.hash(password)
    else:
        # Fallback simples com hashlib
        return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None

def refresh_token_if_needed(token: str) -> str:
    """Verifica se o token precisa ser renovado e retorna um novo se necessário"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        if exp:
            # Se o token expira em menos de 24 horas, renova
            time_until_exp = datetime.fromtimestamp(exp) - datetime.utcnow()
            if time_until_exp.total_seconds() < 86400:  # 24 horas em segundos
                email = payload.get("sub")
                if email:
                    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                    return create_access_token(data={"sub": email}, expires_delta=access_token_expires)
    except JWTError:
        pass
    return token

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = verify_token(credentials.credentials)
    if email is None:
        raise credentials_exception
    
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active or not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not active or verified"
        )
    
    return user