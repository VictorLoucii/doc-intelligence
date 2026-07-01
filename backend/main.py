"""
FastAPI app skeleton — mounts routers and serves the frontend.
Stub only; no route logic yet (route bodies added in S5).
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.routers import documents, query

app = FastAPI(title="N-ERGY Document Intelligence System")

app.include_router(documents.router)
app.include_router(query.router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
