# 1 — Estado atual do seu servidor

Hoje seu servidor funciona aproximadamente assim:

```text
Internet
   │
   ▼
Nginx
   │
   ├── financepowder.cloud  → Flask (127.0.0.1:8000)
   │
   └── n8n.financepowder.cloud → n8n (127.0.0.1:5678)
```

**O que isso significa**
- O Nginx recebe as requisições da internet
- Ele decide para qual serviço enviar
- Os serviços ficam rodando internamente no servidor

**Vantagens dessa arquitetura**
- Apenas uma aplicação exposta na internet (Nginx)
- Backend fica protegido
- HTTPS fica centralizado

---

# 2 — Como chegar nesse estado do zero

Supondo um Ubuntu limpo na VPS.

## 2.1 Atualizar sistema
```bash
sudo apt update
sudo apt upgrade -y
```
**Por quê?** Atualiza a lista de pacotes e corrige vulnerabilidades do sistema.

## 2.2 Instalar Nginx
```bash
sudo apt install nginx -y
```
**O que é o Nginx:** Servidor web de alta performance usado para:
- Servir sites
- Reverse proxy
- Load balancing

## 2.3 Verificar se o nginx está rodando
```bash
systemctl status nginx
```
**Saída esperada:** `active (running)`

**Por quê?** Confirma que o serviço iniciou corretamente.

## 2.4 Liberar portas no firewall

Se estiver usando UFW:
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw reload
```
**O que cada porta significa:**

| Porta | Função |
|---|---|
| 80 | HTTP |
| 443 | HTTPS |

Sem isso o servidor não recebe requisições externas.

## 2.5 Estrutura de configuração do Nginx

No Ubuntu existem duas pastas importantes:
- `/etc/nginx/sites-available`
- `/etc/nginx/sites-enabled`

**Como funciona:**

| Pasta | Função |
|---|---|
| `sites-available` | Todas as configurações possíveis |
| `sites-enabled` | Configurações realmente ativas |

> Ativar site = criar link simbólico.

## 2.6 Criar configuração do site

Criar arquivo: `/etc/nginx/sites-available/financepowder.cloud`

```bash
sudo nano /etc/nginx/sites-available/financepowder.cloud
```

**Configuração inicial:**
```nginx
server {
    listen 80;
    server_name financepowder.cloud www.financepowder.cloud;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Explicação detalhada:**

- **`server`**: Define um host virtual. Cada domínio pode ter um bloco server.
- **`listen 80;`**: Define porta que o nginx escuta.
- **`server_name financepowder.cloud www...;`**: Define quais domínios apontam para esse bloco.
- **`location /`**: Define qual regra será aplicada para a rota. (`/` significa todas as rotas).
- **`proxy_pass http://127.0.0.1:8000;`**: Aqui acontece o reverse proxy. Fluxo: `Browser → Nginx → Flask`
- **`proxy_set_header Host $host;`**: Mantém o domínio original.
- **`proxy_set_header X-Real-IP $remote_addr;`**: Permite que o backend saiba o IP real do usuário.

## 2.7 Ativar o site
```bash
sudo ln -s /etc/nginx/sites-available/financepowder.cloud /etc/nginx/sites-enabled/
```
**Por quê?** O Nginx só carrega configs que estão na pasta `sites-enabled`.

## 2.8 Testar configuração
```bash
sudo nginx -t
```
**Saída esperada:**
```text
syntax is ok
test is successful
```
**Por quê?** Evita reiniciar o nginx com erro de sintaxe.

## 2.9 Recarregar Nginx
```bash
sudo systemctl reload nginx
```
**Diferença importante:**

| Comando | Efeito |
|---|---|
| `reload` | Recarrega a configuração |
| `restart` | Reinicia o serviço inteiro |

> Sempre prefira usar `reload`.

## 2.10 Instalar HTTPS

Instalar certbot:
```bash
sudo apt install certbot python3-certbot-nginx -y
```

Gerar certificado:
```bash
sudo certbot --nginx -d financepowder.cloud -d www.financepowder.cloud
```
**O que acontece aqui:** O Certbot cria o certificado, instala automaticamente no Nginx e configura o redirecionamento para HTTPS.

---

# 3 — Nova arquitetura (React + Flask + Docker)

Agora entra a mudança da arquitetura.

**Antes:**
```text
Nginx → Flask
```

**Agora:**
```text
Nginx → React
      → Flask API
```

**Fluxo:**
```text
Internet
   │
   ▼
Nginx
   │
   ├── /        → React
   │
   ├── /api     → Flask
   │
   └── n8n      → n8n
```

---

# 4 — Como o Docker entra nisso

Cada aplicação roda em containers isolados.

**Exemplo:**
- React container → porta `3000`
- Flask container → porta `8000`

O Nginx apenas encaminha as requisições para a porta interna correta.

---

# 5 — Configuração nginx para React + Flask

Arquivo: `/etc/nginx/sites-available/financepowder.cloud`

**Nova configuração:**
```nginx
server {
    listen 443 ssl;
    server_name financepowder.cloud www.financepowder.cloud;

    ssl_certificate /etc/letsencrypt/live/financepowder.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/financepowder.cloud/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Explicação da nova lógica:**

- **`location /`**: Tudo que não for `/api`. Exemplo: `/home`, `/dashboard`, `/login`. **Vai para o container do React (3000).**
- **`location /api`**: Exemplo: `/api/users`, `/api/login`. **Vai para o container do Flask (8000).**

---

# 6 — Docker Compose do projeto

Cada projeto pode ter seu próprio docker-compose.

**Exemplo (`/projects/financepowder/docker-compose.yml`):**
```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
```

**Por que expor portas?**
`"3000:3000"` significa: `container → host`.
Assim o Nginx acessa no sistema através do endereço local `127.0.0.1:3000`.

---

# 7 — Resultado final da arquitetura

```text
Internet
   │
   ▼
Nginx
   │
   ├── financepowder.cloud
   │      ├── React container
   │      └── Flask container
   │
   └── n8n.financepowder.cloud
          └── n8n container
```

---

# 8 — Importante sobre múltiplos docker-compose

Sim, funciona perfeitamente. Você pode ter:

- `/projects/project1/docker-compose.yml`
- `/projects/project2/docker-compose.yml`
- `/projects/project3/docker-compose.yml`

Cada um expondo portas diferentes:

| Projeto | Porta |
|---|---|
| app1 | 3000 |
| app2 | 3100 |
| app3 | 3200 |

O Nginx decide para qual porto enviar com o `proxy_pass`.

---

# 9 — Mudança real que você vai fazer agora

**Hoje:**
```nginx
proxy_pass http://127.0.0.1:8000;
```

**Novo:**
- `/` → React
- `/api` → Flask

Ou seja, no seu Nginx as rotas ficarão assim:
```nginx
proxy_pass http://127.0.0.1:3000;  # Na rota / (React)
proxy_pass http://127.0.0.1:8000;  # Na rota /api (Flask)
```