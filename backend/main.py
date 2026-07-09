from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
try:
    from database import engine, Base
    from routes import auth, proveedores, facturas, bitacora, reportes
except ImportError:
    from backend.database import engine, Base
    from backend.routes import auth, proveedores, facturas, bitacora, reportes
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartInvoice API",
    description="Sistema inteligente de procesamiento de facturas con OCR y RPA",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(proveedores.router, prefix="/api")
app.include_router(facturas.router, prefix="/api")
app.include_router(bitacora.router, prefix="/api")
app.include_router(reportes.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "SmartInvoice API funcionando"}


frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(os.path.join(frontend_dir, "index.html")):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
