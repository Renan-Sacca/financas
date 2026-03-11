from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.api import routes_banks, routes_cards, routes_transactions, routes_summary, routes_transfers, routes_deposits, routes_categories, routes_auth, routes_bot
from app.config import ALLOWED_ORIGINS

app = FastAPI(title="Finance Control API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

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
app.include_router(routes_bot.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)