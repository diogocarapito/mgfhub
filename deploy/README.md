# Deploy no VPS (transição Streamlit → v3)

Setup real: **nginx no host** a servir mgfhub.com (Streamlit) com
**Cloudflare em modo proxied** à frente. A fase beta é puramente
aditiva — o que serve mgfhub.com hoje não é tocado:

| domínio          | app                          | como                              |
|------------------|------------------------------|-----------------------------------|
| mgfhub.com       | Streamlit atual              | como está (nginx + container)     |
| beta.mgfhub.com  | FastAPI v3 (127.0.0.1:8000)  | novo vhost nginx + compose.beta   |

## Passos

### 1. Cloudflare

Adicionar o registo **A** `beta` → IP do VPS, **proxied** (nuvem
laranja). O certificado universal da Cloudflare já cobre
`beta.mgfhub.com`; o modo SSL do domínio (Flexible/Full/Full strict)
aplica-se igual ao mgfhub.com — não é preciso mudar nada.

### 2. VPS — container v3

```bash
cd mgfhub && git fetch && git checkout v3-fastapi-htmx
cd deploy
docker compose -f compose.beta.yaml up -d --build
curl http://127.0.0.1:8000/healthz     # → {"status":"ok"}
```

O container fica exposto **apenas em localhost** — quem serve o público
é o nginx. Se a porta 8000 já estiver ocupada no VPS:
`MGFHUB_V3_PORT=8010 docker compose -f compose.beta.yaml up -d --build`
(e usar essa porta no `proxy_pass`).

### 3. VPS — vhost nginx

Usar `nginx-beta.conf` como base, **espelhando o server block que já
serve mgfhub.com** (mesmo `listen`/certificados; um certificado
Cloudflare Origin CA cobre `*.mgfhub.com`, por isso os mesmos ficheiros
servem). Só mudam `server_name`, `proxy_pass` e o
`client_max_body_size 25m` (sem ele o nginx rejeita os uploads xlsx
com 413).

```bash
sudo cp nginx-beta.conf /etc/nginx/sites-available/beta.mgfhub.com
# ajustar conforme o vhost existente
sudo ln -s /etc/nginx/sites-available/beta.mgfhub.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 4. Verificar

`https://beta.mgfhub.com` → home da v3; `/indicadores` e `/ide` com um
upload real.

## Atualizar a v3

```bash
cd mgfhub && git pull
cd deploy && docker compose -f compose.beta.yaml up -d --build
```

(As sessões de upload vivem em memória: um rebuild descarta-as — igual
a um restart do Streamlit hoje.)

## Rollback

`docker compose -f compose.beta.yaml down` + remover o vhost. O
mgfhub.com nunca é afetado.

## Alternativa futura: stack completa com Caddy

`compose.yaml` + `Caddyfile` correm as duas apps atrás do Caddy
(ocupa as portas 80/443 — só faz sentido se um dia substituir o nginx).
Com Cloudflare proxied, o modo SSL recomendado nesse cenário é Full
(strict) com certificado Origin CA montado no Caddy, ou desligar o
proxy durante a emissão Let's Encrypt.
