from fastapi import FastAPI, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlmodel import Session, select
from app.database import create_db_and_tables, get_session
from app.models import User
from app.api import routes_banks, routes_cards, routes_transactions, routes_summary, routes_transfers, routes_deposits, routes_categories, routes_auth

app = FastAPI(title="Finance Control API", version="1.0.0")

# Criar tabelas no startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Incluir routers da API
app.include_router(routes_auth.router)
app.include_router(routes_banks.router)
app.include_router(routes_cards.router)
app.include_router(routes_transactions.router)
app.include_router(routes_summary.router)
app.include_router(routes_transfers.router)
app.include_router(routes_deposits.router)
app.include_router(routes_categories.router)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Rotas para servir o frontend
@app.get("/")
async def read_index():
    return FileResponse("frontend/templates/index.html")

@app.get("/login")
async def read_login():
    return FileResponse("frontend/templates/login.html")

@app.get("/register")
async def read_register():
    return FileResponse("frontend/templates/register.html")

# Rota de verificação de email (sem prefixo /api)
@app.get("/verify-email")
def verify_email(token: str = Query(...), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.verification_token == token)).first()
    
    if not user:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Erro de Verificação - Sistema de Finanças</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6 col-lg-4">
                        <div class="card mt-5">
                            <div class="card-header text-center bg-danger text-white">
                                <h3>Token Inválido</h3>
                            </div>
                            <div class="card-body text-center">
                                <div class="mb-3">
                                    <i class="fas fa-times-circle text-danger" style="font-size: 3rem;"></i>
                                </div>
                                <p>O link de verificação é inválido ou já foi usado.</p>
                                <a href="/login" class="btn btn-primary">Voltar ao Login</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)
    
    user.is_verified = True
    user.is_active = True
    user.verification_token = None
    session.add(user)
    session.commit()
    
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verificado - Sistema de Finanças</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6 col-lg-4">
                    <div class="card mt-5">
                        <div class="card-header text-center bg-success text-white">
                            <h3>Email Verificado!</h3>
                        </div>
                        <div class="card-body text-center">
                            <div class="mb-3">
                                <i class="fas fa-check-circle text-success" style="font-size: 3rem;"></i>
                            </div>
                            <p>Sua conta foi ativada com sucesso!</p>
                            <p class="text-muted">Você será redirecionado para o login em <span id="countdown">5</span> segundos...</p>
                            <a href="/login" class="btn btn-primary">Fazer Login Agora</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let countdown = 5;
            const countdownElement = document.getElementById('countdown');
            
            const timer = setInterval(() => {
                countdown--;
                countdownElement.textContent = countdown;
                
                if (countdown <= 0) {
                    clearInterval(timer);
                    window.location.href = '/login';
                }
            }, 1000);
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)