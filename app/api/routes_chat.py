from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.config import N8N_WEBHOOK_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB, CHAT_HISTORY_TTL_DAYS
from app.auth import get_current_user
from app.models import User
import httpx
import io
import csv
import json
import redis
import logging
import tempfile
import os
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])

ALLOWED_EXTENSIONS = {".pdf", ".csv"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
HISTORY_TTL = CHAT_HISTORY_TTL_DAYS * 24 * 3600  # em segundos


# ── Redis client ──────────────────────────────────────────────────────────────
def get_redis() -> Optional[redis.Redis]:
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD or None,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=3,
        )
        r.ping()
        return r
    except Exception as e:
        logger.warning(f"Redis indisponível: {e}")
        return None


def _history_key(session_id: str) -> str:
    return f"chat:history:{session_id}"


def load_history(session_id: str) -> List[dict]:
    r = get_redis()
    if not r:
        return []
    try:
        raw = r.get(_history_key(session_id))
        return json.loads(raw) if raw else []
    except Exception:
        return []


def save_history(session_id: str, history: List[dict]):
    r = get_redis()
    if not r:
        return
    try:
        r.setex(_history_key(session_id), HISTORY_TTL, json.dumps(history, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"Erro ao salvar histórico: {e}")


def clear_history(session_id: str):
    r = get_redis()
    if not r:
        return
    try:
        r.delete(_history_key(session_id))
    except Exception:
        pass


def append_to_history(session_id: str, role: str, text: str):
    history = load_history(session_id)
    history.append({"role": role, "text": text, "ts": datetime.utcnow().isoformat()})
    # Manter no máximo 200 mensagens
    if len(history) > 200:
        history = history[-200:]
    save_history(session_id, history)


# ── Schemas ───────────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    message: str
    session_id: str
    block: Optional[str] = None  # ex: "bank", "card", "transaction", "deposit", "statement_card", "statement_bank", "free"


class ChatResponse(BaseModel):
    reply: str


class HistoryMessage(BaseModel):
    role: str
    text: str
    ts: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[HistoryMessage]


# ── Helpers ───────────────────────────────────────────────────────────────────
def _parse_n8n_response(data) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, list) and len(data) > 0:
        item = data[0]
        return item.get("output", item.get("text", item.get("message", str(item))))
    if isinstance(data, dict):
        return data.get("output", data.get("text", data.get("message", str(data))))
    return str(data)


def _parse_file(content: bytes, ext: str, filename: str) -> list:
    """Usa os parsers do extrator para converter arquivo em lista de transações."""
    from extrator.parsers.csv_parser import parse_csv
    from extrator.parsers.pdf_parser import parse_pdf

    suffix = ext if ext.startswith(".") else f".{ext}"

    # Salva em arquivo temporário pois os parsers esperam filepath
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            return parse_pdf(tmp_path)
        elif suffix == ".csv":
            return parse_csv(tmp_path)
        else:
            return []
    finally:
        os.unlink(tmp_path)


def _extract_pdf_text(content: bytes) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(io.BytesIO(content))
    pages = [p.extract_text().strip() for p in reader.pages if p.extract_text()]
    return "\n\n".join(pages) if pages else "Não foi possível extrair texto do PDF."


def _extract_csv_text(content: bytes) -> str:
    text = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return "Arquivo CSV vazio."
    lines = [" | ".join(row) for row in rows[:200]]
    if len(rows) > 200:
        lines.append(f"... e mais {len(rows) - 200} linhas.")
    return "\n".join(lines)


async def _call_n8n(message: str, session_id: str, extra: dict = None) -> str:
    if not N8N_WEBHOOK_URL:
        raise HTTPException(status_code=503, detail="Chatbot n8n não configurado")
    payload = {"message": message, "session_id": session_id}
    if extra:
        payload.update(extra)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(N8N_WEBHOOK_URL, json=payload)
            resp.raise_for_status()
            return _parse_n8n_response(resp.json())
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout ao contactar o n8n")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Erro do n8n: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ── Rotas de blocos internos (sem n8n) ───────────────────────────────────────
from sqlmodel import Session, select
from app.database import get_session
from app.models import Bank, Card, Transaction, Deposit
from app import crud


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_chat_history(session_id: str, current_user: User = Depends(get_current_user)):
    history = load_history(session_id)
    return HistoryResponse(
        session_id=session_id,
        messages=[HistoryMessage(**m) for m in history],
    )


@router.delete("/history/{session_id}")
async def delete_chat_history(session_id: str, current_user: User = Depends(get_current_user)):
    clear_history(session_id)
    return {"message": "Histórico limpo com sucesso"}


# ── BLOCO 1: BANCO ────────────────────────────────────────────────────────────
class BankActionRequest(BaseModel):
    session_id: str
    action: str  # "create" | "update_balance" | "list"
    name: Optional[str] = None
    bank_id: Optional[int] = None
    balance: Optional[float] = None


@router.post("/bank", response_model=ChatResponse)
async def chat_bank(
    payload: BankActionRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    reply = ""

    if payload.action == "create":
        if not payload.name:
            raise HTTPException(status_code=400, detail="Nome do banco é obrigatório")
        from app.schemas import BankCreate
        bank = crud.create_bank(db, BankCreate(name=payload.name, current_balance=payload.balance or 0.0), current_user.id)
        reply = f"✅ Banco *{bank.name}* criado com saldo R$ {bank.current_balance:.2f}."

    elif payload.action == "update_balance":
        if not payload.bank_id or payload.balance is None:
            raise HTTPException(status_code=400, detail="bank_id e balance são obrigatórios")
        from app.schemas import BankUpdate
        bank = crud.update_bank(db, payload.bank_id, BankUpdate(current_balance=payload.balance), current_user.id)
        if not bank:
            raise HTTPException(status_code=404, detail="Banco não encontrado")
        reply = f"✅ Saldo do banco *{bank.name}* atualizado para R$ {bank.current_balance:.2f}."

    elif payload.action == "list":
        banks = crud.get_banks(db, current_user.id)
        if not banks:
            reply = "Nenhum banco cadastrado ainda."
        else:
            lines = ["🏦 *Seus bancos:*"]
            for b in banks:
                lines.append(f"• [{b.id}] {b.name} — R$ {b.current_balance:.2f}")
            reply = "\n".join(lines)
    else:
        raise HTTPException(status_code=400, detail="Ação inválida")

    append_to_history(payload.session_id, "user", f"[BANCO:{payload.action}]")
    append_to_history(payload.session_id, "bot", reply)
    return ChatResponse(reply=reply)


# ── BLOCO 2: CARTÃO ───────────────────────────────────────────────────────────
class CardActionRequest(BaseModel):
    session_id: str
    action: str  # "create" | "edit" | "list" | "limit"
    bank_id: Optional[int] = None
    card_id: Optional[int] = None
    name: Optional[str] = None
    card_type: Optional[str] = None  # "credit" | "debit"
    limit_amount: Optional[float] = None
    due_day: Optional[int] = None


@router.post("/card", response_model=ChatResponse)
async def chat_card(
    payload: CardActionRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    reply = ""

    if payload.action == "create":
        if not payload.bank_id or not payload.name or not payload.card_type:
            raise HTTPException(status_code=400, detail="bank_id, name e card_type são obrigatórios")
        bank = crud.get_bank(db, payload.bank_id, current_user.id)
        if not bank:
            raise HTTPException(status_code=404, detail="Banco não encontrado")
        from app.schemas import CardCreate
        from app.models import CardType
        ct = CardType.credit if payload.card_type == "credit" else CardType.debit
        card = crud.create_card(db, payload.bank_id, CardCreate(
            name=payload.name, type=ct,
            limit_amount=payload.limit_amount, due_day=payload.due_day
        ))
        reply = f"✅ Cartão *{card.name}* ({payload.card_type}) criado no banco *{bank.name}*."
        if payload.limit_amount:
            reply += f" Limite: R$ {payload.limit_amount:.2f}."

    elif payload.action == "edit":
        if not payload.card_id:
            raise HTTPException(status_code=400, detail="card_id é obrigatório")
        from app.schemas import CardUpdate
        from app.models import CardType
        update = CardUpdate(
            name=payload.name,
            limit_amount=payload.limit_amount,
            due_day=payload.due_day,
        )
        if payload.card_type:
            update.type = CardType.credit if payload.card_type == "credit" else CardType.debit
        card = crud.update_card(db, payload.card_id, update, current_user.id)
        if not card:
            raise HTTPException(status_code=404, detail="Cartão não encontrado")
        reply = f"✅ Cartão *{card.name}* atualizado."

    elif payload.action == "list":
        cards = crud.get_cards(db, current_user.id)
        if not cards:
            reply = "Nenhum cartão cadastrado ainda."
        else:
            lines = ["💳 *Seus cartões:*"]
            for c in cards:
                bank = crud.get_bank(db, c.bank_id, current_user.id)
                bank_name = bank.name if bank else "?"
                lim = f" | Limite: R$ {c.limit_amount:.2f}" if c.limit_amount else ""
                lines.append(f"• [{c.id}] {c.name} ({c.type.value}) — {bank_name}{lim}")
            reply = "\n".join(lines)

    elif payload.action == "limit":
        cards = crud.get_cards(db, current_user.id)
        credit_cards = [c for c in cards if c.type.value == "credit"]
        if not credit_cards:
            reply = "Nenhum cartão de crédito encontrado."
        else:
            lines = ["💳 *Limite disponível:*"]
            for c in credit_cards:
                if c.limit_amount:
                    # Calcular usado no mês atual
                    from datetime import date
                    today = date.today()
                    used = db.exec(
                        select(Transaction).where(
                            Transaction.card_id == c.id,
                            Transaction.date >= date(today.year, today.month, 1),
                        )
                    ).all()
                    used_total = sum(t.amount for t in used)
                    available = c.limit_amount - used_total
                    lines.append(f"• {c.name}: R$ {available:.2f} disponível de R$ {c.limit_amount:.2f}")
                else:
                    lines.append(f"• {c.name}: sem limite cadastrado")
            reply = "\n".join(lines)
    else:
        raise HTTPException(status_code=400, detail="Ação inválida")

    append_to_history(payload.session_id, "user", f"[CARTÃO:{payload.action}]")
    append_to_history(payload.session_id, "bot", reply)
    return ChatResponse(reply=reply)


# ── BLOCO 3: GASTOS COM CARTÃO ────────────────────────────────────────────────
class TransactionActionRequest(BaseModel):
    session_id: str
    card_id: int
    amount: float
    description: str
    date: str  # YYYY-MM-DD
    category_id: Optional[int] = None
    total_installments: Optional[int] = None


@router.post("/transaction", response_model=ChatResponse)
async def chat_transaction(
    payload: TransactionActionRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from datetime import date as date_type
    import uuid

    card = db.exec(
        select(Card).join(Bank).where(Card.id == payload.card_id, Bank.user_id == current_user.id)
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")

    purchase_date = date_type.fromisoformat(payload.date)
    due_day = card.due_day or 1

    def calc_due(purchase: date_type, due_d: int, offset_months: int = 0) -> date_type:
        m = purchase.month + offset_months
        y = purchase.year
        while m > 12:
            m -= 12
            y += 1
        if purchase.day > due_d:
            m += 1
            if m > 12:
                m = 1
                y += 1
        return date_type(y, m, due_d)

    installments = payload.total_installments or 1

    if installments > 1:
        group_id = str(uuid.uuid4())
        inst_amount = round(payload.amount / installments, 2)
        for i in range(installments):
            due = calc_due(purchase_date, due_day, i)
            t = Transaction(
                card_id=payload.card_id,
                amount=inst_amount,
                description=f"{payload.description} ({i+1}/{installments})",
                date=due,
                purchase_date=purchase_date,
                category_id=payload.category_id,
                group_id=group_id,
                installment_number=i + 1,
                total_installments=installments,
                created_via="bot",
            )
            db.add(t)
        db.commit()
        reply = f"✅ Compra *{payload.description}* de R$ {payload.amount:.2f} em {installments}x de R$ {inst_amount:.2f} adicionada no cartão *{card.name}*."
    else:
        due = calc_due(purchase_date, due_day)
        t = Transaction(
            card_id=payload.card_id,
            amount=payload.amount,
            description=payload.description,
            date=due,
            purchase_date=purchase_date,
            category_id=payload.category_id,
            created_via="bot",
        )
        db.add(t)
        db.commit()
        reply = f"✅ Gasto *{payload.description}* de R$ {payload.amount:.2f} adicionado no cartão *{card.name}* (venc. {due.strftime('%d/%m/%Y')})."

    append_to_history(payload.session_id, "user", f"[GASTO] {payload.description} R${payload.amount}")
    append_to_history(payload.session_id, "bot", reply)
    return ChatResponse(reply=reply)


# ── BLOCO 4: DEPÓSITO ─────────────────────────────────────────────────────────
class DepositActionRequest(BaseModel):
    session_id: str
    bank_id: int
    amount: float
    description: Optional[str] = None
    date: str  # YYYY-MM-DD
    type_id: int = 1
    payment_method_id: int = 1
    add_to_balance: bool = True


@router.post("/deposit", response_model=ChatResponse)
async def chat_deposit(
    payload: DepositActionRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from datetime import date as date_type
    from app.schemas import DepositCreate

    bank = db.exec(select(Bank).where(Bank.id == payload.bank_id, Bank.user_id == current_user.id)).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Banco não encontrado")

    dep = crud.create_deposit(
        db,
        DepositCreate(
            bank_id=payload.bank_id,
            amount=payload.amount,
            description=payload.description,
            type_id=payload.type_id,
            payment_method_id=payload.payment_method_id,
            date=date_type.fromisoformat(payload.date),
            add_to_balance=payload.add_to_balance,
        ),
        current_user.id,
        payload.add_to_balance,
    )

    reply = f"✅ Depósito de R$ {payload.amount:.2f} adicionado no banco *{bank.name}*."
    if payload.add_to_balance:
        db.refresh(bank)
        reply += f" Novo saldo: R$ {bank.current_balance:.2f}."

    append_to_history(payload.session_id, "user", f"[DEPÓSITO] R${payload.amount} em {bank.name}")
    append_to_history(payload.session_id, "bot", reply)
    return ChatResponse(reply=reply)


# ── BLOCO 5: EXTRATO FATURA CARTÃO (upload) ───────────────────────────────────
@router.post("/statement/card", response_model=ChatResponse)
async def chat_statement_card(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    card_id: int = Form(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from app.models import PendingStatementItem
    import uuid as uuid_mod
    from datetime import date as date_type

    filename = (file.filename or "").lower()
    ext = next((e for e in ALLOWED_EXTENSIONS if filename.endswith(e)), None)
    if not ext:
        raise HTTPException(status_code=400, detail=f"Envie PDF ou CSV. Recebido: {filename}")

    # Validar que o cartão pertence ao usuário
    card = db.exec(
        select(Card).join(Bank).where(Card.id == card_id, Bank.user_id == current_user.id)
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 5MB")

    try:
        transacoes = _parse_file(content, ext, file.filename or "arquivo")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erro ao processar arquivo: {e}")
    finally:
        del content

    if not transacoes:
        reply = "⚠️ Nenhuma transação encontrada no arquivo."
        append_to_history(session_id, "user", f"[EXTRATO CARTÃO] {file.filename}")
        append_to_history(session_id, "bot", reply)
        return ChatResponse(reply=reply)

    # Salvar na tabela provisória
    batch_id = str(uuid_mod.uuid4())
    for t in transacoes:
        # Converter data DD/MM/YYYY → date
        raw_date = t.get("data", "")
        try:
            if raw_date and "/" in raw_date:
                parts = raw_date.split("/")
                data_compra = date_type(int(parts[2]), int(parts[1]), int(parts[0]))
            elif raw_date:
                data_compra = date_type.fromisoformat(raw_date)
            else:
                data_compra = date_type.today()
        except Exception:
            data_compra = date_type.today()

        item = PendingStatementItem(
            batch_id=batch_id,
            user_id=current_user.id,
            card_id=card_id,
            descricao=t.get("descricao", "Sem descrição")[:500],
            valor=float(t.get("valor", 0)),
            data_compra=data_compra,
            tipo=t.get("tipo", "outros"),
            filename=file.filename,
        )
        db.add(item)
    db.commit()

    base_url = "https://financepowder.cloud"
    link = f"{base_url}/pending/{batch_id}"
    reply = (
        f"✅ *{len(transacoes)} transação(ões)* do cartão *{card.name}* salvas para revisão!\n\n"
        f"Acesse o link abaixo para revisar e confirmar antes de salvar nas faturas:\n"
        f"🔗 {link}"
    )

    append_to_history(session_id, "user", f"[EXTRATO CARTÃO] {file.filename}")
    append_to_history(session_id, "bot", reply)
    return ChatResponse(reply=reply)


# ── BLOCO 6: EXTRATO BANCO (upload) ───────────────────────────────────────────
@router.post("/statement/bank", response_model=ChatResponse)
async def chat_statement_bank(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    message: str = Form(default=""),
    current_user: User = Depends(get_current_user),
):
    filename = (file.filename or "").lower()
    ext = next((e for e in ALLOWED_EXTENSIONS if filename.endswith(e)), None)
    if not ext:
        raise HTTPException(status_code=400, detail=f"Envie PDF ou CSV. Recebido: {filename}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 5MB")

    try:
        transacoes = _parse_file(content, ext, file.filename or "arquivo")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erro ao processar arquivo: {e}")
    finally:
        del content

    if not transacoes:
        reply = "⚠️ Nenhuma transação encontrada no arquivo."
    else:
        reply = f"🏛️ *Extrato Banco — {len(transacoes)} transação(ões) encontrada(s):*\n\n"
        reply += json.dumps(transacoes, ensure_ascii=False, indent=2)

    append_to_history(session_id, "user", f"[EXTRATO BANCO] {file.filename}")
    append_to_history(session_id, "bot", reply)
    return ChatResponse(reply=reply)


# ── BLOCO 7: MENSAGEM LIVRE (compras via n8n) ─────────────────────────────────
@router.post("", response_model=ChatResponse)
async def send_chat_message(
    payload: ChatMessage,
    current_user: User = Depends(get_current_user),
):
    """Bloco 7 — mensagem livre de compras, interpretada pelo n8n."""
    reply = await _call_n8n(payload.message, payload.session_id, {"block": "free_purchase"})
    append_to_history(payload.session_id, "user", payload.message)
    append_to_history(payload.session_id, "bot", reply)
    return ChatResponse(reply=reply or "Desculpe, não consegui processar sua mensagem.")
