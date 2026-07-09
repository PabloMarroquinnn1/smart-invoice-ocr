from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Factura, Bitacora
from services.report_service import generar_reporte_pdf, generar_reporte_excel, generar_reporte_csv
from services.email_service import enviar_reporte_email
from services.rpa_service import ejecutar_rpa
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/reportes", tags=["Reportes y RPA"])


@router.get("/pdf")
def descargar_reporte_pdf(db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.estado == "Procesado").all()
    if not facturas:
        raise HTTPException(status_code=404, detail="No hay facturas procesadas")
    filepath = generar_reporte_pdf(facturas)
    log = Bitacora(accion="GENERAR_REPORTE", documento="reporte.pdf",
                   estado="Éxito", resultado=f"Reporte PDF con {len(facturas)} facturas")
    db.add(log); db.commit()
    return FileResponse(filepath, filename="reporte_facturas.pdf", media_type="application/pdf")


@router.get("/excel")
def descargar_reporte_excel(db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.estado == "Procesado").all()
    if not facturas:
        raise HTTPException(status_code=404, detail="No hay facturas procesadas")
    filepath = generar_reporte_excel(facturas)
    log = Bitacora(accion="GENERAR_REPORTE", documento="reporte.xlsx",
                   estado="Éxito", resultado=f"Reporte Excel con {len(facturas)} facturas")
    db.add(log); db.commit()
    return FileResponse(filepath, filename="reporte_facturas.xlsx",
                       media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/csv")
def descargar_reporte_csv(db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.estado == "Procesado").all()
    if not facturas:
        raise HTTPException(status_code=404, detail="No hay facturas procesadas")
    filepath = generar_reporte_csv(facturas)
    log = Bitacora(accion="GENERAR_REPORTE", documento="reporte.csv",
                   estado="Éxito", resultado=f"Reporte CSV con {len(facturas)} facturas")
    db.add(log); db.commit()
    return FileResponse(filepath, filename="reporte_facturas.csv", media_type="text/csv")


class EmailRequest(BaseModel):
    destinatario: str
    formato: Optional[str] = "pdf"

@router.post("/email")
def enviar_reporte(data: EmailRequest, db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.estado == "Procesado").all()
    if not facturas:
        raise HTTPException(status_code=404, detail="No hay facturas procesadas")
    if data.formato == "excel":
        filepath = generar_reporte_excel(facturas)
    elif data.formato == "csv":
        filepath = generar_reporte_csv(facturas)
    else:
        filepath = generar_reporte_pdf(facturas)
    resultado = enviar_reporte_email(data.destinatario, filepath)
    log = Bitacora(accion="ENVIO_EMAIL", documento=f"reporte.{data.formato}",
                   estado="Éxito" if resultado["status"] == "ok" else "Error",
                   resultado=resultado["mensaje"])
    db.add(log); db.commit()
    return resultado


@router.post("/rpa/ejecutar/{factura_id}")
def ejecutar_rpa_factura(factura_id: int, request: Request, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    base_url = str(request.base_url).rstrip('/')
    form_url = f"{base_url}/api/reportes/rpa/form"

    factura_data = {
        "numero_factura": factura.numero_factura,
        "nombre_proveedor": factura.nombre_proveedor or "",
        "nit_proveedor": factura.nit_proveedor or "",
        "fecha": factura.fecha or "",
        "cliente_nombre": factura.cliente_nombre or "",
        "subtotal": factura.subtotal,
        "impuestos": factura.impuestos,
        "total": factura.total,
    }

    resultado = ejecutar_rpa(factura_data, form_url)

    log = Bitacora(
        accion="RPA_REGISTRO_AUTOMATICO",
        documento=factura.numero_factura,
        estado="Éxito" if resultado["status"] == "ok" else "Error",
        resultado=resultado["mensaje"]
    )
    db.add(log); db.commit()
    return resultado


class RegistroRPA(BaseModel):
    numero_factura: str
    proveedor: str
    nit: str
    fecha: str
    cliente: str
    subtotal: str
    iva: str
    total: str

@router.post("/rpa/registrar")
def registrar_factura_rpa(data: RegistroRPA, db: Session = Depends(get_db)):
    log = Bitacora(
        accion="RPA_FORMULARIO_RECIBIDO",
        documento=data.numero_factura,
        estado="Éxito",
        resultado=f"Registro RPA: {data.numero_factura} | Proveedor: {data.proveedor} | Total: Q{data.total}"
    )
    db.add(log)
    db.commit()

    return {"status": "ok", "mensaje": f"Factura {data.numero_factura} registrada por RPA"}


@router.get("/rpa/registros")
def ver_registros_rpa(db: Session = Depends(get_db)):
    registros = db.query(Bitacora).filter(
        Bitacora.accion.in_(["RPA_REGISTRO_AUTOMATICO", "RPA_FORMULARIO_RECIBIDO"])
    ).order_by(Bitacora.fecha_hora.desc()).all()
    return [{"fecha": r.fecha_hora.isoformat(), "documento": r.documento,
             "estado": r.estado, "resultado": r.resultado} for r in registros]


@router.get("/rpa/form", response_class=HTMLResponse)
def formulario_rpa():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Sistema Contable - Registro de Facturas</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #e8eaf6; padding: 30px; margin: 0; }
            .header { background: #1a237e; color: #fff; padding: 15px 30px; margin: -30px -30px 30px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { font-size: 18px; margin: 0; }
            .header a { color: #90caf9; text-decoration: none; font-size: 13px; }
            .form-container { max-width: 650px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
            h2 { color: #1a237e; margin-bottom: 5px; }
            .subtitle { color: #888; font-size: 13px; margin-bottom: 20px; }
            .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
            .form-grid .full { grid-column: span 2; }
            label { display: block; font-size: 12px; font-weight: 600; color: #555; margin-bottom: 4px; text-transform: uppercase; }
            input { width: 100%; padding: 10px 12px; border: 1.5px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }
            input:focus { outline: none; border-color: #1a237e; }
            .btn-submit { margin-top: 20px; padding: 12px 24px; background: #1a237e; color: #fff; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; width: 100%; font-weight: 600; }
            .btn-submit:hover { background: #0d1642; }
            .success { display: none; background: #c8e6c9; color: #2e7d32; padding: 15px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: 600; border: 1px solid #a5d6a7; }
            .timestamp { color: #aaa; font-size: 11px; text-align: center; margin-top: 15px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Sistema Contable ERP - Módulo de Facturas</h1>
            <a href="/">← Volver a SmartInvoice</a>
        </div>
        <div class="form-container">
            <h2>Registro de Factura</h2>
            <p class="subtitle">Módulo de registro automático de facturas</p>

            <div class="form-grid">
                <div>
                    <label>Número de Factura</label>
                    <input type="text" id="rpa-numero">
                </div>
                <div>
                    <label>Fecha</label>
                    <input type="text" id="rpa-fecha">
                </div>
                <div>
                    <label>Proveedor</label>
                    <input type="text" id="rpa-proveedor">
                </div>
                <div>
                    <label>NIT</label>
                    <input type="text" id="rpa-nit">
                </div>
                <div class="full">
                    <label>Cliente</label>
                    <input type="text" id="rpa-cliente">
                </div>
                <div>
                    <label>Subtotal (Q)</label>
                    <input type="text" id="rpa-subtotal">
                </div>
                <div>
                    <label>IVA 12% (Q)</label>
                    <input type="text" id="rpa-iva">
                </div>
                <div class="full">
                    <label>Total (Q)</label>
                    <input type="text" id="rpa-total" style="font-size:18px;font-weight:700">
                </div>
            </div>

            <button class="btn-submit" id="rpa-submit" onclick="registrarFactura()">Registrar en Sistema</button>
            <div class="success" id="msg"></div>
            <div class="timestamp" id="ts"></div>
        </div>

        <script>
        async function registrarFactura() {
            const data = {
                numero_factura: document.getElementById('rpa-numero').value,
                proveedor: document.getElementById('rpa-proveedor').value,
                nit: document.getElementById('rpa-nit').value,
                fecha: document.getElementById('rpa-fecha').value,
                cliente: document.getElementById('rpa-cliente').value,
                subtotal: document.getElementById('rpa-subtotal').value,
                iva: document.getElementById('rpa-iva').value,
                total: document.getElementById('rpa-total').value
            };

            try {
                const r = await fetch('/api/reportes/rpa/registrar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await r.json();
                const msg = document.getElementById('msg');
                msg.style.display = 'block';
                msg.textContent = 'Factura ' + data.numero_factura + ' registrada exitosamente en el sistema contable.';
                document.getElementById('ts').textContent = 'Registrado: ' + new Date().toLocaleString('es-GT');
                document.getElementById('rpa-submit').disabled = true;
                document.getElementById('rpa-submit').textContent = 'Registrado';
                document.getElementById('rpa-submit').style.background = '#4caf50';
            } catch(e) {
                alert('Error: ' + e.message);
            }
        }
        </script>
    </body>
    </html>
    """
