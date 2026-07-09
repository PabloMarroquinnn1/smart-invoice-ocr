# SmartInvoice — Invoice Processing with OCR & Computer Vision

Plataforma inteligente para el procesamiento automatico de facturas que integra Computer Vision (OpenCV), OCR (Tesseract) y RPA (Selenium). Permite cargar facturas en PDF, JPG o PNG, extraer automaticamente la informacion contenida, almacenarla en base de datos y ejecutar procesos automatizados como generacion de reportes, envio de correos y registro en sistemas externos.

## Tecnologias

| Componente | Tecnologia |
|---|---|
| Backend / API | Python + FastAPI |
| OCR | Tesseract + pytesseract |
| Computer Vision | OpenCV |
| RPA | Selenium (headless) |
| Base de datos | SQLite + SQLAlchemy |
| Frontend | HTML, CSS, JavaScript |
| Reportes | ReportLab (PDF), openpyxl (Excel) |
| Email | SMTP (Gmail) |
| Contenedores | Docker + Docker Compose |

## Arquitectura (MVC + Servicios)

```
┌─────────────────────────────────────┐
│          Frontend (Vista)           │
│     HTML + CSS + JavaScript         │
│  Login, Dashboard, Carga Facturas,  │
│  Reportes, Bitacora                 │
└──────────────┬──────────────────────┘
               │ HTTP (fetch)
┌──────────────▼──────────────────────┐
│      FastAPI Backend (Controlador)  │
│  routes/: auth, facturas,           │
│  proveedores, reportes, bitacora    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Capa de Servicios            │
│  ocr_service    → Tesseract+OpenCV  │
│  report_service → PDF/Excel/CSV     │
│  email_service  → SMTP Gmail        │
│  rpa_service    → Selenium headless │
└──────────────┬──────────────────────┘
               │ SQLAlchemy ORM
┌──────────────▼──────────────────────┐
│            SQLite                   │
│  Tablas: users, invoices,           │
│  providers, audit_log               │
└─────────────────────────────────────┘
```

## Caracteristicas

- **OCR inteligente:** Extraccion automatica de datos de facturas (proveedor, NIT, montos, items) usando Tesseract y OpenCV
- **Computer Vision:** Preprocesamiento de imagenes (escala de grises, threshold, deteccion de contornos) para mejorar la precision del OCR
- **RPA:** Bot Selenium que registra facturas automaticamente en sistemas externos
- **Reportes:** Generacion de reportes en PDF, Excel y CSV con envio automatico por email
- **Dashboard:** Panel con estadisticas de facturas procesadas, montos y proveedores
- **Autenticacion:** Sistema de login/registro con JWT
- **Bitacora:** Registro completo de todas las acciones del sistema
- **Dockerizado:** Despliegue con Docker Compose

## Requisitos

- Docker Desktop 4.x+
- Git

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/PabloMarroquinnn1/smart-invoice-ocr.git
cd smart-invoice-ocr
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales (Gmail para envio de reportes, etc.).

### 3. Levantar los servicios

```bash
docker-compose up --build
```

La aplicacion estara disponible en `http://localhost:8000`.

## Estructura del proyecto

```
├── backend/
│   ├── main.py                  # Entry point FastAPI
│   ├── database.py              # Conexion SQLAlchemy + SQLite
│   ├── models.py                # Modelos ORM
│   ├── schemas.py               # Validacion Pydantic
│   ├── requirements.txt
│   ├── routes/
│   │   ├── auth.py              # Login / Registro
│   │   ├── facturas.py          # Upload y gestion de facturas
│   │   ├── proveedores.py       # CRUD proveedores
│   │   ├── bitacora.py          # Consulta de historial
│   │   └── reportes.py          # Reportes, email y RPA
│   ├── services/
│   │   ├── ocr_service.py       # Tesseract + OpenCV
│   │   ├── report_service.py    # PDF / Excel / CSV
│   │   ├── email_service.py     # SMTP Gmail
│   │   └── rpa_service.py       # Selenium headless
│   └── uploads/                 # Archivos subidos
├── frontend/
│   ├── index.html               # Vista principal
│   ├── css/styles.css           # Estilos
│   └── js/app.js                # Logica del frontend
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── docs/
    ├── ManualTecnico.md         # Documentacion tecnica
    └── ManualUsuario.md         # Guia de uso
```

## Documentacion

- [Manual Tecnico](docs/ManualTecnico.md) — Arquitectura MVC, servicios OCR/CV/RPA, modelos
- [Manual de Usuario](docs/ManualUsuario.md) — Instalacion y guia paso a paso

## Autor

**Pablo Alejandro Marroquin Cutz**
