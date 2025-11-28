# Sistema de Controle de Finanças Pessoais

Sistema completo para controle de finanças pessoais com backend FastAPI, banco SQLite e frontend HTML/Bootstrap/JavaScript.

## Funcionalidades

- ✅ **Sistema de Autenticação Completo**
  - Cadastro de usuários com confirmação por email
  - Login seguro com JWT
  - Isolamento de dados por usuário
- ✅ Cadastro de bancos com saldo inicial
- ✅ Criação de cartões (crédito/débito) vinculados aos bancos
- ✅ Registro de transações (despesas, pagamentos, reembolsos)
- ✅ Cálculo automático de saldos por banco e total geral
- ✅ Histórico completo de transações com filtros
- ✅ Interface responsiva com Bootstrap
- ✅ API REST documentada (OpenAPI/Swagger)

## Tecnologias

- **Backend**: FastAPI + SQLModel + MySQL
- **Frontend**: HTML5 + Bootstrap 5 + JavaScript (Fetch API)
- **Containerização**: Docker + Docker Compose

## Como executar

### Configuração Inicial

1. **Configurar variáveis de ambiente**:
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas configurações de email
# Para Gmail, use uma senha de app: https://support.google.com/accounts/answer/185833
```

### Com Docker (Recomendado)

```bash
# Clonar/baixar o projeto
cd finance-app

# Construir e executar
docker-compose up --build

# Acessar a aplicação
# Frontend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Desenvolvimento local

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Primeiro Acesso

1. Acesse http://localhost:8000
2. Clique em "Cadastre-se" para criar uma conta
3. Verifique seu email e clique no link de confirmação
4. Faça login com suas credenciais

## Estrutura do Projeto

```
finance-app/
├── app/                    # Backend FastAPI
│   ├── main.py            # Aplicação principal
│   ├── models.py          # Modelos SQLModel
│   ├── schemas.py         # Schemas Pydantic
│   ├── crud.py            # Operações CRUD
│   ├── database.py        # Configuração do banco
│   └── api/               # Rotas da API
├── frontend/              # Frontend
│   ├── static/           # CSS e JavaScript
│   └── templates/        # HTML
├── data/                 # Dados locais (backup SQLite)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## API Endpoints

### Bancos
- `GET /api/banks/` - Listar bancos
- `POST /api/banks/` - Criar banco
- `GET /api/banks/{id}` - Detalhes do banco
- `DELETE /api/banks/{id}` - Excluir banco
- `POST /api/banks/{id}/cards` - Adicionar cartão ao banco

### Cartões
- `GET /api/cards/` - Listar cartões

### Transações
- `POST /api/transactions/` - Criar transação
- `GET /api/transactions/` - Listar transações

### Resumo
- `GET /api/summary/` - Resumo financeiro

## Exemplos de Uso (curl)

### Criar banco
```bash
curl -X POST "http://localhost:8000/api/banks/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Banco do Brasil", "initial_balance": 1000.0}'
```

### Adicionar cartão
```bash
curl -X POST "http://localhost:8000/api/banks/1/cards" \
  -H "Content-Type: application/json" \
  -d '{"name": "Visa Crédito", "type": "credit"}'
```

### Registrar despesa
```bash
curl -X POST "http://localhost:8000/api/transactions/" \
  -H "Content-Type: application/json" \
  -d '{
    "card_id": 1,
    "amount": 150.50,
    "type": "expense",
    "description": "Compras supermercado",
    "date": "2024-01-15"
  }'
```

### Obter resumo
```bash
curl "http://localhost:8000/api/summary/"
```

## Lógica de Saldo

O saldo atual de cada banco é calculado como:
```
Saldo Atual = Saldo Inicial + Pagamentos + Reembolsos - Despesas
```

- **Despesas**: Reduzem o saldo do banco
- **Pagamentos/Reembolsos**: Aumentam o saldo do banco
- Cartões de crédito e débito afetam o saldo do banco igualmente (simplificação para MVP)

## Dados de Teste

Após fazer login, você pode:

1. Criar um banco (ex: "Nubank") com saldo inicial R$ 500,00
2. Adicionar cartões (ex: "Nubank Crédito" e "Nubank Débito")
3. Registrar algumas transações de teste
4. Verificar o resumo financeiro atualizado

**Nota**: Cada usuário tem seus próprios dados isolados. Bancos, cartões e transações são privados para cada conta.

## Desenvolvimento

Para adicionar novas funcionalidades:

1. **Modelos**: Editar `app/models.py`
2. **API**: Adicionar rotas em `app/api/`
3. **Frontend**: Modificar `frontend/templates/index.html` e `frontend/static/js/app.js`

## Migração para MySQL

### Configuração do Banco

1. **Configurar MySQL na VPS**:
```bash
# Configurar banco de dados
python setup_mysql.py
```

2. **Migrar dados do SQLite (se existir)**:
```bash
# Migrar dados existentes
python migrate_to_mysql.py
```

3. **Usar configuração de produção**:
```bash
# Copiar configurações para produção
cp .env.production .env
```

### Variáveis de Ambiente MySQL

```bash
MYSQL_HOST=72.60.140.18
MYSQL_PORT=3306
MYSQL_USER=user_pessoal
MYSQL_PASSWORD=Re+991352443
MYSQL_DATABASE=financas_db
```

## Melhorias Futuras

- [x] Autenticação JWT
- [x] Isolamento de dados por usuário
- [x] Confirmação de email
- [x] Migração para MySQL
- [ ] Recuperação de senha
- [ ] Filtros avançados por data
- [ ] Exportação CSV
- [ ] Gráficos interativos
- [ ] Categorização de gastos
- [ ] Metas de economia
- [ ] Notificações de limite
- [ ] Autenticação com Google/Facebook