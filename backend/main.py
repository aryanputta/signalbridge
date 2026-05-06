from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_db
from routers import signals, patients, patterns

app = FastAPI(title="SignalBridge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db()


app.include_router(signals.router)
app.include_router(patients.router)
app.include_router(patterns.router)


@app.get("/health")
def health():
    return {"status": "ok"}
