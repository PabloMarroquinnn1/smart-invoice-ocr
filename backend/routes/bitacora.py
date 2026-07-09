from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Bitacora
from schemas import BitacoraResponse
from typing import List

router = APIRouter(prefix="/bitacora", tags=["Bitácora"])


@router.get("/", response_model=List[BitacoraResponse])
def listar_bitacora(db: Session = Depends(get_db)):
    return db.query(Bitacora).order_by(Bitacora.fecha_hora.desc()).all()
