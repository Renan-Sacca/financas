from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import create_db_and_tables
from app.migrate import migrate_database
from app.api import routes_banks, routes_cards, routes_transactions, routes_summary, routes_transfers, routes_deposits

app = FastAPI(title="Finance Control API", version="1.0.0")

# Criar tabelas no startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    migrate_database()

# Incluir routers da API
app.include_router(routes_banks.router)
app.include_router(routes_cards.router)
app.include_router(routes_transactions.router)
app.include_router(routes_summary.router)
app.include_router(routes_transfers.router)
app.include_router(routes_deposits.router)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Rota para servir o frontend
@app.get("/")
async def read_index():
    return FileResponse("frontend/templates/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)