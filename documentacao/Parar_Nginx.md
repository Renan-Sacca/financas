# 1 — Verificar se o Nginx está rodando

```bash
sudo systemctl status nginx
```

Ou, alternativamente:

```bash
ps aux | grep nginx
```

---

# 2 — Parar o Nginx

Para testar Traefik, você pode parar o serviço temporariamente:

```bash
sudo systemctl stop nginx
```

---

# 3 — Impedir o Nginx de subir no boot

Se você pretende migrar totalmente para Traefik, é bom desativar o início automático:

```bash
sudo systemctl disable nginx
```

---

# 4 — Verificar se as portas ficaram livres

```bash
sudo lsof -i :80
sudo lsof -i :443
```

> **Nota:** Se não aparecer nada após rodar os comandos acima → **as portas estão livres.**