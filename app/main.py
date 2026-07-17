"""Entrypoint da app FastAPI (mgfhub v3).

Correr localmente:
    make run-v3        (uvicorn com reload em http://localhost:8000)
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import home, ide, indicadores
from app.templating import BASE_DIR

app = FastAPI(title="mgfhub", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


app.include_router(home.router)
app.include_router(indicadores.router)
app.include_router(ide.router)
