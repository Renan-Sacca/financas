from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from datetime import timedelta
from app.database import get_session
from app.models import User
from app.schemas import UserCreate, UserLogin, Token, UserResponse
from app.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from app.email_service import send_verification_email, generate_verification_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=dict)
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    # Verificar se email já existe
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Criar usuário
    verification_token = generate_verification_token()
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        verification_token=verification_token
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    # Enviar email de verificação
    email_sent = send_verification_email(user.email, verification_token)
    
    return {
        "message": "User registered successfully. Please check your email to verify your account.",
        "email_sent": email_sent
    }

@router.post("/login", response_model=Token)
def login_user(user: UserLogin, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please check your email."
        )
    
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/verify-email")
def verify_email(token: str = Query(...), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.verification_token == token)).first()
    
    if not user:
        return HTMLResponse("""
        <html><body>
        <h2>Token inválido ou expirado</h2>
        <p>O link de verificação é inválido ou já foi usado.</p>
        <a href="/">Voltar ao site</a>
        </body></html>
        """)
    
    user.is_verified = True
    user.is_active = True
    user.verification_token = None
    session.add(user)
    session.commit()
    
    return HTMLResponse("""
    <html><body>
    <h2>Email verificado com sucesso!</h2>
    <p>Sua conta foi ativada. Você já pode fazer login.</p>
    <a href="/">Fazer Login</a>
    </body></html>
    """)

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user