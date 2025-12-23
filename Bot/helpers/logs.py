#imports independientes
import os, time
from datetime import datetime


def tomar_screenshot(driver, ruta_logs: str, nombre="error"):
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    #carpeta = os.path.join(ruta_logs, "screenshots")

    os.makedirs(ruta_logs, exist_ok=True)
    ruta = os.path.join(ruta_logs, f"{nombre}_{fecha}.png")
    time.sleep(1)
    driver.save_screenshot(ruta)
    return ruta

def registrar_log(ruta_logs: str, mensaje: str, tipo="INFO"):
    os.makedirs(ruta_logs, exist_ok=True)
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ruta_archivo = os.path.join(ruta_logs, f"log_{fecha_hoy}.txt")
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    linea = f"[{timestamp}] [{tipo.upper()}] - {mensaje}\n"
    
    with open(ruta_archivo, "a", encoding="utf-8") as f:
        f.write(linea)
    
    return ruta_archivo