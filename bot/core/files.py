# bot/core/files.py
from __future__ import annotations
import os
from typing import Optional, List
from loguru import logger

CSF_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}

class ActosFinder:
    """
    Utilidades para ubicar carpetas/archivos de actos en el sistema local.
    """

    @staticmethod
    def compraventa_path(root_dir: str, nombre_carpeta: str = "Compraventa Daniel") -> str:
        """
        Regresa la ruta absoluta a la carpeta del acto de compraventa.
        No valida existencia; usa ensure_* para validar.
        """
        return os.path.join(os.path.abspath(root_dir), nombre_carpeta)

    @staticmethod
    def ensure_dir(path: str, label: str) -> bool:
        if not os.path.isdir(path):
            logger.error("No existe la carpeta {} -> {}", label, path)
            return False
        logger.debug("Carpeta {} OK -> {}", label, path)
        return True

    @staticmethod
    def find_csf_in_comprador(comprador_dir: str) -> Optional[str]:
        """
        Busca un archivo de CSF dentro de la carpeta del Comprador.
        Criterios:
          - nombre contenga 'csf' o 'constancia de situacion fiscal' (insensible a may/min)
          - extensión en CSF_EXTS
        Devuelve la ruta si la encuentra; None si no.
        """
        if not os.path.isdir(comprador_dir):
            logger.error("No existe la carpeta 'Comprador' -> {}", comprador_dir)
            return None

        targets: List[str] = []
        try:
            for name in os.listdir(comprador_dir):
                full = os.path.join(comprador_dir, name)
                if not os.path.isfile(full):
                    continue
                base_lower = name.lower()
                _, ext = os.path.splitext(name)
                if ext.lower() not in CSF_EXTS:
                    continue
                if ("csf" in base_lower) or ("constancia de situacion fiscal" in base_lower):
                    targets.append(full)
        except Exception as e:
            logger.exception("Error leyendo carpeta Comprador: {}", e)
            return None

        if not targets:
            logger.warning("No se encontró archivo de CSF en {}", comprador_dir)
            return None

        # Heurística simple: prioriza PDFs si hay varios
        targets.sort(key=lambda p: (0 if p.lower().endswith(".pdf") else 1, p.lower()))
        elegido = targets[0]
        logger.info("CSF localizado: {}", elegido)
        return elegido
