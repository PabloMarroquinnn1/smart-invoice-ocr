import re
import os
import cv2
import numpy as np
import pytesseract


def procesar_factura_ocr(filepath: str) -> dict:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        text = _ocr_pdf(filepath)
    else:
        text = _ocr_image(filepath)

    print("=" * 60)
    print("TEXTO EXTRAIDO:")
    print(text)
    print("=" * 60)

    datos = _parsear_factura(text)
    datos["texto_crudo"] = text
    return datos


def _ocr_image(filepath: str) -> str:
    img = cv2.imread(filepath)
    if img is None:
        raise Exception(f"No se pudo leer la imagen: {filepath}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape
    if w < 1500:
        scale = 1500 / w
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    denoised = cv2.medianBlur(thresh, 3)

    config = '--oem 3 --psm 6 -l spa'
    text = pytesseract.image_to_string(denoised, config=config)
    return text


def _ocr_pdf(filepath: str) -> str:
    try:
        import fitz
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        if text.strip():
            return text

        doc = fitz.open(filepath)
        page = doc[0]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_path = filepath + "_temp.png"
        pix.save(img_path)
        doc.close()

        result = _ocr_image(img_path)
        try:
            os.remove(img_path)
        except:
            pass
        return result

    except ImportError:
        raise Exception("PyMuPDF no instalado. Ejecute: pip install PyMuPDF")


def _parsear_factura(text: str) -> dict:
    datos = {
        "numero_factura": "",
        "proveedor": "",
        "nit": "",
        "fecha": "",
        "cliente_nombre": "",
        "cliente_direccion": "",
        "subtotal": 0.0,
        "impuestos": 0.0,
        "total": 0.0,
        "items": []
    }

    m = re.search(r'FAC[-\s]*(\d{3,6})', text, re.IGNORECASE)
    if m:
        datos["numero_factura"] = f"FAC-{m.group(1).zfill(5)}"
    else:
        m = re.search(r'\b(0{2,}\d{1,4})\b', text)
        if m:
            datos["numero_factura"] = f"FAC-{m.group(1)}"

    m = re.search(r'Proveedor[:\s]+(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        datos["proveedor"] = m.group(1).strip()

    m = re.search(r'NIT[:\.\s]+(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        nit = m.group(1).strip()
        nit = re.sub(r'[^\d\-]', '', nit)
        if nit:
            datos["nit"] = nit

    m = re.search(r'Fecha[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', text, re.IGNORECASE)
    if m:
        datos["fecha"] = m.group(1).strip()

    m = re.search(r'Cliente[:\s]*\n\s*(.+?)(?:\n)', text, re.IGNORECASE)
    if m:
        datos["cliente_nombre"] = m.group(1).strip()

    m = re.search(r'Cliente[:\s]*\n\s*.+?\n\s*(.+?)(?:\n)', text, re.IGNORECASE)
    if m:
        datos["cliente_direccion"] = m.group(1).strip()

    m = re.search(r'Subtotal[:\s]*Q?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
    if m:
        datos["subtotal"] = _parse_monto(m.group(1))

    m = re.search(r'IVA\s*\d*\s*%?\s*[:\s]*Q?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
    if m:
        datos["impuestos"] = _parse_monto(m.group(1))

    totales = re.findall(r'TOTAL[:\s]*Q?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
    if totales:
        montos = [_parse_monto(t) for t in totales]
        datos["total"] = max(montos)

    if datos["subtotal"] == 0 and datos["total"] > 0 and datos["impuestos"] > 0:
        datos["subtotal"] = round(datos["total"] - datos["impuestos"], 2)
    if datos["impuestos"] == 0 and datos["subtotal"] > 0 and datos["total"] > 0:
        datos["impuestos"] = round(datos["total"] - datos["subtotal"], 2)

    datos["items"] = _parsear_items(text)

    if datos["subtotal"] == 0 and datos["items"]:
        datos["subtotal"] = round(sum(item["total"] for item in datos["items"]), 2)

    return datos


def _parsear_items(text: str) -> list:
    items = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^(Cant|Subtotal|IVA|TOTAL|FACTURA|Proveedor|NIT|Fecha|Cliente|Documento|Descripci)', line, re.IGNORECASE):
            continue

        m = re.match(r'^(\d{1,2})\s+(.+?)\s+Q\s*([\d,.]+)\s+Q\s*([\d,.]+)', line)
        if m:
            item = _crear_item(m.group(1), m.group(2), m.group(3), m.group(4))
            if item:
                items.append(item)
                continue

        m = re.match(r'^(\d{1,2})\s+(.+?)\s+Q([\d,.]+)\s+Q([\d,.]+)', line)
        if m:
            item = _crear_item(m.group(1), m.group(2), m.group(3), m.group(4))
            if item:
                items.append(item)
                continue

        m = re.match(r'^(\d{1,2})\s+([A-Za-zÀ-ÿ]\w*(?:\s+\w+)*?)\s+([\d,.]+)\s+([\d,.]+)\s*$', line)
        if m:
            precio = _parse_monto(m.group(3))
            total = _parse_monto(m.group(4))
            cant = int(m.group(1))
            if precio > 5 and total > 5:
                items.append({
                    "cantidad": cant,
                    "descripcion": m.group(2).strip(),
                    "precio": precio,
                    "total": total
                })

    return items


def _crear_item(cant_str, desc, precio_str, total_str):
    try:
        cant = int(cant_str)
        precio = _parse_monto(precio_str)
        total = _parse_monto(total_str)
        desc = desc.strip()
        if cant < 1 or cant > 99:
            return None
        if precio <= 0 or total <= 0:
            return None
        if len(desc) < 1 or len(desc) > 100:
            return None
        if desc.lower() in ['cant', 'descripcion', 'precio', 'total']:
            return None
        return {"cantidad": cant, "descripcion": desc, "precio": precio, "total": total}
    except (ValueError, TypeError):
        return None


def _parse_monto(texto: str) -> float:
    try:
        return float(texto.replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0
