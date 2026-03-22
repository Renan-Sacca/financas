from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import N8N_WEBHOOK_URL
import httpx

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])


class ChatMessage(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
async def send_chat_message(payload: ChatMessage):
    if not N8N_WEBHOOK_URL:
        raise HTTPException(status_code=503, detail="Chatbot não configurado")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                N8N_WEBHOOK_URL,
                json={"message": payload.message, "session_id": payload.session_id},
            )
            resp.raise_for_status()
            data = resp.json()

            # n8n pode retornar em diferentes formatos
            if isinstance(data, str):
                return ChatResponse(reply=data)
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                return ChatResponse(
                    reply=item.get("output", item.get("text", item.get("message", str(item))))
                )
            if isinstance(data, dict):
                return ChatResponse(
                    reply=data.get("output", data.get("text", data.get("message", str(data))))
                )

            return ChatResponse(reply=str(data))

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout ao contactar o chatbot")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Erro do chatbot: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
