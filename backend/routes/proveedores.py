from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Proveedor
from schemas import ProveedorCreate, ProveedorUpdate, ProveedorResponse
from typing import List

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])


@router.get("/", response_model=List[ProveedorResponse])
def listar_proveedores(db: Session = Depends(get_db)):
    return db.query(Proveedor).all()


@router.get("/{proveedor_id}", response_model=ProveedorResponse)
def obtener_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return prov


@router.post("/", response_model=ProveedorResponse)
def crear_proveedor(data: ProveedorCreate, db: Session = Depends(get_db)):
    prov = Proveedor(**data.model_dump())
    db.add(prov)
    db.commit()
    db.refresh(prov)
    return prov


@router.put("/{proveedor_id}", response_model=ProveedorResponse)
def actualizar_proveedor(proveedor_id: int, data: ProveedorUpdate, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(prov, key, value)
    db.commit()
    db.refresh(prov)
    return prov


@router.delete("/{proveedor_id}")
def eliminar_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    db.delete(prov)
    db.commit()
    return {"message": "Proveedor eliminado exitosamente"}
