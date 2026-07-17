# Deploy no VPS (transição Streamlit → v3)

Um único `docker compose` corre as duas apps atrás do Caddy, que trata
do HTTPS automaticamente (Let's Encrypt):

| domínio          | app                          |
|------------------|------------------------------|
| mgfhub.com       | Streamlit atual (porta 8501) |
| beta.mgfhub.com  | FastAPI v3 (porta 8000)      |

## Pré-requisitos

1. Registos DNS **A** de `mgfhub.com`, `www.mgfhub.com` e `beta.mgfhub.com`
   a apontar para o IP do VPS.
2. Docker + docker compose no VPS.
3. Portas **80 e 443 livres** — parar primeiro o que estiver a servir a
   app atualmente (container antigo, nginx, etc.), senão o Caddy não
   arranca.

## Primeira instalação

```bash
git clone https://github.com/diogocarapito/mgfhub
cd mgfhub
git checkout v3-fastapi-htmx        # até ao merge para master

# opcional: telemetria supabase da app streamlit
# echo "SUPABASE_URL=..."  > .env
# echo "SUPABASE_KEY=..." >> .env

cd deploy
docker compose up -d --build
docker compose ps                    # os 3 serviços devem ficar healthy
docker compose logs caddy | tail     # confirmar a emissão dos certificados
```

## Atualizar

```bash
cd mgfhub && git pull
cd deploy && docker compose up -d --build
```

## Rollback

O rollback da v3 é parar o serviço (`docker compose stop mgfhub-v3`) —
o mgfhub.com continua a ser servido pela app Streamlit, que não é
afetada. Para reverter tudo ao mecanismo de deploy antigo:
`docker compose down` e repor o serviço anterior.

## Notas

- Os certificados e a configuração do Caddy ficam nos volumes
  `caddy_data`/`caddy_config` — sobrevivem a rebuilds.
- A v3 corre num único processo e guarda as sessões de upload em
  memória: um `up -d --build` descarta as sessões ativas (os
  utilizadores voltam a carregar os xlsx — igual ao comportamento de um
  restart do Streamlit hoje).
