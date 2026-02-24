from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .webapp import app as api_app
from .webapp_ui import ui_app

app = FastAPI(title="Procurement Webapp", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api", api_app)
app.mount("", ui_app)
