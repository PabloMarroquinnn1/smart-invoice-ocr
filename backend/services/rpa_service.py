import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def ejecutar_rpa(factura_data: dict, form_url: str) -> dict:
    driver = None
    screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    os.makedirs(screenshots_dir, exist_ok=True)

    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280,900')

        driver = webdriver.Chrome(options=options)

        driver.get(form_url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "rpa-numero")))
        time.sleep(0.5)

        campos = {
            "rpa-numero": str(factura_data.get("numero_factura", "")),
            "rpa-proveedor": str(factura_data.get("nombre_proveedor", "")),
            "rpa-nit": str(factura_data.get("nit_proveedor", "")),
            "rpa-fecha": str(factura_data.get("fecha", "")),
            "rpa-cliente": str(factura_data.get("cliente_nombre", "")),
            "rpa-subtotal": str(factura_data.get("subtotal", 0)),
            "rpa-iva": str(factura_data.get("impuestos", 0)),
            "rpa-total": str(factura_data.get("total", 0)),
        }

        for field_id, value in campos.items():
            element = driver.find_element(By.ID, field_id)
            element.clear()
            element.send_keys(value)
            time.sleep(0.2)

        fac_id = factura_data.get("numero_factura", "unknown").replace("-", "")
        screenshot_before = os.path.join(screenshots_dir, f"rpa_antes_{fac_id}.png")
        driver.save_screenshot(screenshot_before)

        submit_btn = driver.find_element(By.ID, "rpa-submit")
        submit_btn.click()
        time.sleep(1.5)

        screenshot_after = os.path.join(screenshots_dir, f"rpa_despues_{fac_id}.png")
        driver.save_screenshot(screenshot_after)

        driver.quit()

        return {
            "status": "ok",
            "mensaje": f"RPA completado: factura {factura_data.get('numero_factura')} registrada automáticamente en el sistema contable simulado",
            "screenshots": {
                "antes": screenshot_before,
                "despues": screenshot_after
            }
        }

    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        return {
            "status": "error",
            "mensaje": f"Error en RPA: {str(e)}"
        }
