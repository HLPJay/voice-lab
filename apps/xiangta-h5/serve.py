"""Minimal static file server for apps/xiangta-h5 preview."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
_h5_dir = str(Path(__file__).parent)
app.mount("/", StaticFiles(directory=_h5_dir, html=True), name="h5")
