"""Entrypoint da app FastAPI (mgfhub v3).

Correr localmente:
    make run-v3        (uvicorn com reload em http://localhost:8000)
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import conta, home, ide, indicadores, legal
from app.templating import BASE_DIR

app = FastAPI(title="mgfhub", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.middleware("http")
async def cache_de_estaticos(request, call_next):
    """Os assets levam ?v=<hash do conteúdo> nos URLs, por isso podem ser
    cacheados indefinidamente (browser e Cloudflare) — um deploy que os
    mude gera URLs novos."""
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


app.include_router(home.router)
app.include_router(indicadores.router)
app.include_router(ide.router)
app.include_router(conta.router)
app.include_router(legal.router)
