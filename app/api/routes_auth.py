from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from datetime import timedelta
from app.database import get_session
from app.models import User
from app.schemas import UserCreate, UserLogin, Token, UserResponse, PasswordResetRequest, PasswordReset, UserUpdate
from app.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from app.email_service import send_verification_email, generate_verification_token, send_password_reset_email

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
        telefone=user.telefone,
        id_telegram=user.id_telegram,
        username_telegram=user.username_telegram,
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

@router.put("/me", response_model=UserResponse)
def update_current_user(user_update: UserUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.telefone is not None:
        current_user.telefone = user_update.telefone
    if user_update.id_telegram is not None:
        current_user.id_telegram = user_update.id_telegram
    if user_update.username_telegram is not None:
        current_user.username_telegram = user_update.username_telegram
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user

@router.post("/forgot-password")
def forgot_password(request: PasswordResetRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == request.email)).first()
    
    if not user:
        # Por segurança, sempre retornamos sucesso mesmo se o email não existir
        return {"message": "Se o email existir, um link de redefinição foi enviado."}
    
    # Gerar token de reset
    reset_token = generate_verification_token()
    user.reset_token = reset_token
    session.add(user)
    session.commit()
    
    # Enviar email
    email_sent = send_password_reset_email(user.email, reset_token)
    
    return {
        "message": "Se o email existir, um link de redefinição foi enviado.",
        "email_sent": email_sent
    }

@router.post("/reset-password")
def reset_password(request: PasswordReset, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.reset_token == request.token)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    # Atualizar senha
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_token = None  # Limpar token após uso
    session.add(user)
    session.commit()
    
    return {"message": "Senha redefinida com sucesso"}

@router.get("/reset-password")
def reset_password_page(token: str = Query(...)):
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Redefinir Senha - Sistema de Finanças</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6 col-lg-4">
                    <div class="card mt-5">
                        <div class="card-header text-center">
                            <h3>Redefinir Senha</h3>
                        </div>
                        <div class="card-body">
                            <form id="resetForm">
                                <input type="hidden" id="token" value="{token}">
                                <div class="mb-3">
                                    <label for="newPassword" class="form-label">Nova Senha</label>
                                    <input type="password" class="form-control" id="newPassword" required minlength="6">
                                </div>
                                <div class="mb-3">
                                    <label for="confirmPassword" class="form-label">Confirmar Nova Senha</label>
                                    <input type="password" class="form-control" id="confirmPassword" required minlength="6">
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Redefinir Senha</button>
                            </form>
                            <div id="message" class="mt-3"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.getElementById('resetForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const token = document.getElementById('token').value;
                const newPassword = document.getElementById('newPassword').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                const messageDiv = document.getElementById('message');
                
                if (newPassword !== confirmPassword) {{
                    messageDiv.innerHTML = '<div class="alert alert-danger">As senhas não coincidem.</div>';
                    return;
                }}
                
                try {{
                    const response = await fetch('/api/auth/reset-password', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ token, new_password: newPassword }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        messageDiv.innerHTML = '<div class="alert alert-success">Senha redefinida com sucesso! Redirecionando...</div>';
                        setTimeout(() => {{
                            window.location.href = '/login';
                        }}, 2000);
                    }} else {{
                        messageDiv.innerHTML = `<div class="alert alert-danger">${{data.detail}}</div>`;
                    }}
                }} catch (error) {{
                    messageDiv.innerHTML = '<div class="alert alert-danger">Erro ao redefinir senha. Tente novamente.</div>';
                }}
            }});
        </script>
    </body>
    </html>
    """)