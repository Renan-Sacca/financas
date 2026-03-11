# 1 — Problema da arquitetura tradicional (Nginx)

Na arquitetura que você usa hoje, o fluxo é o seguinte:

```text
Internet
   │
   ▼
Nginx
   │
   ├── projeto1 → porta 3000
   ├── projeto2 → porta 3100
   ├── projeto3 → porta 3200
```

**Sempre que você cria um novo projeto, precisa:**
1. Editar o Nginx
2. Criar um novo server block
3. Reiniciar o Nginx
4. Configurar o SSL manualmente

Isso acaba gerando muita manutenção manual.

---

# 2 — Arquitetura moderna (Traefik)

Traefik é um reverse proxy moderno que detecta containers automaticamente.

**Nova Arquitetura:**
```text
Internet
   │
   ▼
Traefik
   │
   ├── projeto React
   ├── API Flask
   ├── n8n
   └── outros projetos
```

O Traefik observa o **Docker socket** e cria as rotas automaticamente conforme os containers sobem.

---

# 3 — Fluxo de funcionamento

Quando você sobe um container com as "labels" corretas:
1. Você roda o comando `docker compose up`.
2. O Traefik detecta o novo container.
3. Ele cria a rota automaticamente.

**Fluxo de acesso:**
```text
financepowder.cloud
        │
        ▼
     Traefik
        │
        ▼
   container React
```

---

# 4 — SSL automático

O Traefik possui integração nativa com o **Let's Encrypt**.

**Resultado:**
Todos os seus domínios e subdomínios (ex: `financepowder.cloud`, `api.financepowder.cloud`, `tracker.financepowder.cloud`) recebem SSL automaticamente, sem a necessidade de rodar o `certbot` manualmente.

---

# 5 — Estrutura da VPS

Uma sugestão de organização de pastas:

```text
/docker
   /traefik
       docker-compose.yml

/projects
   /financepowder
       docker-compose.yml
   /tracker
       docker-compose.yml
   /n8n
       docker-compose.yml
```
> Cada projeto mantém seu próprio arquivo `docker-compose.yml`.

---

# 6 — Docker network compartilhada

Para que o Traefik consiga se comunicar com os outros containers, todos precisam estar na mesma rede Docker:

```bash
docker network create proxy
```

Essa rede permite que o Traefik "enxergue" e encaminhe tráfego para todos os serviços.

---

# 7 — Docker Compose do Traefik

Arquivo: `/docker/traefik/docker-compose.yml`

```yaml
version: "3"

services:
  traefik:
    image: traefik:v3
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=seuemail@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt
    networks:
      - proxy

networks:
  proxy:
    external: true
```

---

# 8 — Explicação das partes importantes

- **`docker.sock` (`/var/run/docker.sock`)**: Permite que o Traefik monitore os eventos do Docker e veja quais containers estão rodando.
- **`entrypoints`**: Define as portas públicas que o Traefik vai escutar (`80` para HTTP e `443` para HTTPS).
- **`certificatesresolvers`**: Configura o Let's Encrypt para geração automática de certificados.

---

# 9 — Subindo o Traefik

Para iniciar o serviço do Traefik:

```bash
docker compose up -d
```

A partir do momento em que ele subir, passará a escutar as portas 80 e 443.

---

# 10 — Exemplo de projeto React + Flask

Agora, cada projeto define seu domínio e regras diretamente dentro do seu próprio `docker-compose.yml` através de **labels**.

Arquivo: `/projects/financepowder/docker-compose.yml`

```yaml
version: "3"

services:
  frontend:
    build: ./frontend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.financepowder.rule=Host(`financepowder.cloud`)"
      - "traefik.http.routers.financepowder.entrypoints=websecure"
      - "traefik.http.routers.financepowder.tls.certresolver=letsencrypt"
    networks:
      - proxy

  backend:
    build: ./backend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.financepowder-api.rule=Host(`financepowder.cloud`) && PathPrefix(`/api`)"
      - "traefik.http.routers.financepowder-api.entrypoints=websecure"
      - "traefik.http.routers.financepowder-api.tls.certresolver=letsencrypt"
    networks:
      - proxy

networks:
  proxy:
    external: true
```

---

# 11 — O que acontece aqui

A label `traefik.http.routers.financepowder.rule=Host('financepowder.cloud')` diz ao Traefik:
> "Se chegar uma requisição para o domínio `financepowder.cloud`, envie para este container."

---

# 12 — API Flask

A regra `PathPrefix('/api')` no backend garante o roteamento correto:
- `/api/v1/users` → Redireciona para o container **Flask**.
- `/home` ou `/login` → Redireciona para o container **React** (por cair na regra geral `/`).

---

# 13 — Resultado final

```text
Internet
   │
   ▼
Traefik
   │
   ├── financepowder.cloud
   │      ├── React
   │      └── Flask API
   │
   ├── tracker.cloud
   │      └── API
   │
   ├── n8n.cloud
   │      └── n8n
```

---

# 14 — Grande vantagem

Quando você criar um novo projeto, basta rodar:

```bash
docker compose up -d
```

O Traefik fará tudo sozinho:
1. Cria a rota.
2. Gera o certificado SSL.
3. Publica o domínio.

**Sem precisar mexer em arquivos de configuração do proxy nunca mais!**