from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    bitacoras = relationship("Bitacora", back_populates="usuario")


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    nit = Column(String(20), nullable=False)
    direccion = Column(String(300))
    telefono = Column(String(20))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    facturas = relationship("Factura", back_populates="proveedor")


class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, index=True)
    numero_factura = Column(String(50), nullable=False)
    fecha = Column(String(20))
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    nit_proveedor = Column(String(20))
    nombre_proveedor = Column(String(200))
    cliente_nombre = Column(String(200))
    cliente_direccion = Column(String(300))
    subtotal = Column(Float, default=0.0)
    impuestos = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    estado = Column(String(20), default="Pendiente")
    archivo_original = Column(String(500))
    texto_extraido = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    proveedor = relationship("Proveedor", back_populates="facturas")
    detalles = relationship("DetalleFactura", back_populates="factura", cascade="all, delete-orphan")


class DetalleFactura(Base):
    __tablename__ = "detalle_facturas"

    id = Column(Integer, primary_key=True, index=True)
    factura_id = Column(Integer, ForeignKey("facturas.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    descripcion = Column(String(200))
    precio_unitario = Column(Float, default=0.0)
    total_linea = Column(Float, default=0.0)

    factura = relationship("Factura", back_populates="detalles")


class Bitacora(Base):
    __tablename__ = "bitacora"

    id = Column(Integer, primary_key=True, index=True)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    accion = Column(String(100))
    documento = Column(String(500))
    estado = Column(String(50))
    resultado = Column(Text)

    usuario = relationship("Usuario", back_populates="bitacoras")
