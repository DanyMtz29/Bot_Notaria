from loguru import logger
import os
from datetime import datetime

#Para quitar los logs en consola
logger.remove()

"""
    ARCHIVO DE LOGGER:
    Crear un archivo de logs por dias
    Guarda los logs correspondientes en la carpeta que se le pase
"""
def setup_logger(nombre_carpeta: str):

    #Qyitar los anteriores
    logger.remove()

    # 1. Crear carpeta si no existe
    log_dir = os.path.join("bot", "logs", nombre_carpeta)
    os.makedirs(log_dir, exist_ok=True)

    # 2. Crear archivo del día
    fecha = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{fecha}.log")

    # 3. Agregar handler si no está registrado
    logger.add(
        log_file,
        encoding="utf-8",
        enqueue=True,
        backtrace=False,
        diagnose=False,   
        level="INFO"
    )
