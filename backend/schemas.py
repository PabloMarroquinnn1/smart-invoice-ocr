from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UsuarioCreate(BaseModel):
    username: str
    password: str
    nombre: Optional[str] = None
    email: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class UsuarioResponse(BaseModel):
    id: int
    username: str
    nombre: Optional[str]
    email: Optional[str]
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse


class ProveedorCreate(BaseModel):
    nombre: str
    nit: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    nit: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class ProveedorResponse(BaseModel):
    id: int
    nombre: str
    nit: str
    direccion: Optional[str]
    telefono: Optional[str]
    email: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


class DetalleFacturaResponse(BaseModel):
    id: int
    cantidad: int
    descripcion: Optional[str]
    precio_unitario: float
    total_linea: float
    class Config:
        from_attributes = True

class FacturaResponse(BaseModel):
    id: int
    numero_factura: str
    fecha: Optional[str]
    nombre_proveedor: Optional[str]
    nit_proveedor: Optional[str]
    cliente_nombre: Optional[str]
    cliente_direccion: Optional[str]
    subtotal: float
    impuestos: float
    total: float
    estado: str
    archivo_original: Optional[str]
    created_at: datetime
    detalles: List[DetalleFacturaResponse] = []
    class Config:
        from_attributes = True


class BitacoraResponse(BaseModel):
    id: int
    fecha_hora: datetime
    usuario_id: Optional[int]
    accion: Optional[str]
    documento: Optional[str]
    estado: Optional[str]
    resultado: Optional[str]
    class Config:
        from_attributes = True
