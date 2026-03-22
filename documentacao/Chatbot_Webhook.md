# Chatbot - Integração com n8n via Webhook

## Visão Geral

O chatbot da aplicação funciona como um proxy: o frontend envia a mensagem para o backend FastAPI (`POST /api/chat`), que repassa para o webhook do n8n e devolve a resposta ao usuário.

```
Usuário → Frontend → Backend (FastAPI) → n8n Webhook → Backend → Frontend → Usuário
```

---

## Endpoint do Backend

**`POST /api/chat`**

### Request Body

```json
{
  "message": "texto digitado pelo usuário",
  "session_id": "session_1719432000000_a1b2c3d"
}
```

| Campo        | Tipo   | Obrigatório | Descrição                                                                 |
|--------------|--------|-------------|---------------------------------------------------------------------------|
| `message`    | string | Sim         | Texto da mensagem enviada pelo usuário                                    |
| `session_id` | string | Sim         | Identificador único da sessão do chat (gerado no frontend por sessão)     |

### Response Body (sucesso - 200)

```json
{
  "reply": "texto da resposta do bot"
}
```

### Erros possíveis

| Status | Descrição                                      |
|--------|-------------------------------------------------|
| 503    | `N8N_WEBHOOK_URL` não configurada no `.env`     |
| 504    | Timeout ao contactar o n8n (limite: 30s)        |
| 502    | n8n retornou erro HTTP                          |
| 500    | Erro interno inesperado                         |

---

## O que é enviado ao n8n (Webhook)

**Método:** `POST`  
**URL:** Configurada na variável de ambiente `N8N_WEBHOOK_URL`  
**Content-Type:** `application/json`

### Body enviado ao n8n

```json
{
  "message": "texto digitado pelo usuário",
  "session_id": "session_1719432000000_a1b2c3d"
}
```

| Campo        | Tipo   | Descrição                                                                 |
|--------------|--------|---------------------------------------------------------------------------|
| `message`    | string | Mensagem do usuário para o bot processar                                  |
| `session_id` | string | ID da sessão para manter contexto da conversa entre mensagens             |

---

## O que o backend espera receber do n8n

O backend tenta interpretar a resposta do n8n em 3 formatos possíveis:

### Formato 1 - String simples
```json
"Aqui está a resposta do bot"
```

### Formato 2 - Array de objetos
```json
[
  {
    "output": "Aqui está a resposta do bot"
  }
]
```
Campos procurados (em ordem de prioridade): `output`, `text`, `message`

### Formato 3 - Objeto simples
```json
{
  "output": "Aqui está a resposta do bot"
}
```
Campos procurados (em ordem de prioridade): `output`, `text`, `message`

---

## Configuração

### Variável de ambiente (back_end/.env)

```env
N8N_WEBHOOK_URL=https://n8n.financepowder.cloud/webhook-test/a4ca9bf8-9034-44bd-8a02-1f1064f18e05
```

### Timeout

O backend aguarda no máximo **30 segundos** pela resposta do n8n antes de retornar erro 504.

---

## Exemplo de fluxo completo

1. Usuário digita "Qual meu saldo?" no chat
2. Frontend faz `POST /api/chat` com `{"message": "Qual meu saldo?", "session_id": "session_xxx"}`
3. Backend repassa para o webhook do n8n com o mesmo body
4. n8n processa e retorna `{"output": "Seu saldo atual é R$ 1.500,00"}`
5. Backend extrai o campo `output` e retorna `{"reply": "Seu saldo atual é R$ 1.500,00"}`
6. Frontend exibe a mensagem na janela do chat
