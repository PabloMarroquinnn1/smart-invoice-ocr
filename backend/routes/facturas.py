from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session
from database import get_db
from models import Factura, DetalleFactura, Proveedor, Bitacora
from schemas import FacturaResponse
from routes.auth import get_current_user
from typing import List, Optional
from services.ocr_service import procesar_factura_ocr
import os
import shutil
from datetime import datetime

router = APIRouter(prefix="/facturas", tags=["Facturas"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=FacturaResponse)
async def upload_factura(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    allowed = [".pdf", ".jpg", ".jpeg", ".png"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Formato no permitido. Use: {allowed}")

    user_id = None
    if authorization:
        try:
            user = get_current_user(authorization, db)
            user_id = user.id
        except:
            pass

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    log = Bitacora(
        usuario_id=user_id, accion="CARGA_FACTURA",
        documento=filename, estado="Éxito",
        resultado=f"Archivo {filename} cargado correctamente"
    )
    db.add(log)
    db.commit()

    try:
        datos = procesar_factura_ocr(filepath)

        proveedor_id = None
        if datos.get("nit"):
            prov = db.query(Proveedor).filter(Proveedor.nit == datos["nit"]).first()
            if not prov:
                prov = Proveedor(
                    nombre=datos.get("proveedor", "Desconocido"),
                    nit=datos["nit"]
                )
                db.add(prov)
                db.commit()
                db.refresh(prov)
            proveedor_id = prov.id

        factura = Factura(
            numero_factura=datos.get("numero_factura", "N/A"),
            fecha=datos.get("fecha", ""),
            proveedor_id=proveedor_id,
            nombre_proveedor=datos.get("proveedor", ""),
            nit_proveedor=datos.get("nit", ""),
            cliente_nombre=datos.get("cliente_nombre", ""),
            cliente_direccion=datos.get("cliente_direccion", ""),
            subtotal=datos.get("subtotal", 0.0),
            impuestos=datos.get("impuestos", 0.0),
            total=datos.get("total", 0.0),
            estado="Procesado",
            archivo_original=filename,
            texto_extraido=datos.get("texto_crudo", "")
        )
        db.add(factura)
        db.commit()
        db.refresh(factura)

        for item in datos.get("items", []):
            detalle = DetalleFactura(
                factura_id=factura.id,
                cantidad=item.get("cantidad", 1),
                descripcion=item.get("descripcion", ""),
                precio_unitario=item.get("precio", 0.0),
                total_linea=item.get("total", 0.0)
            )
            db.add(detalle)
        db.commit()
        db.refresh(factura)

        suma_items = sum(d.total_linea for d in factura.detalles)
        validacion = "OK" if abs(suma_items - factura.subtotal) < 0.1 else \
            f"DISCREPANCIA: suma items={suma_items}, subtotal={factura.subtotal}"

        log2 = Bitacora(
            usuario_id=user_id, accion="OCR_PROCESAMIENTO",
            documento=filename, estado="Éxito",
            resultado=f"Factura {datos.get('numero_factura')} procesada. Validación: {validacion}"
        )
        db.add(log2)
        db.commit()

        return factura

    except Exception as e:
        factura = Factura(
            numero_factura="ERROR", estado="Error",
            archivo_original=filename, texto_extraido=str(e)
        )
        db.add(factura)
        log_err = Bitacora(
            usuario_id=user_id, accion="OCR_PROCESAMIENTO",
            documento=filename, estado="Error",
            resultado=f"Error: {str(e)}"
        )
        db.add(log_err)
        db.commit()
        db.refresh(factura)
        return factura


@router.get("/", response_model=List[FacturaResponse])
def listar_facturas(db: Session = Depends(get_db)):
    return db.query(Factura).order_by(Factura.created_at.desc()).all()


@router.get("/{factura_id}", response_model=FacturaResponse)
def obtener_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura


@router.delete("/{factura_id}")
def eliminar_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    db.delete(factura)
    db.commit()
    return {"message": "Factura eliminada"}
