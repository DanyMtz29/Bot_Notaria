# bot/models/person_docs.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class PersonDocs:
    nombre: Optional[str] = None
    rfc: Optional[str] = None
    idcif: Optional[str] = None

    # Rutas de archivos
    paths: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "CSF": None,
        "CURP": None,
        "ACTA_NAC": None,
        "INE": None,
        "COMP_DOMICILIO": None,   # opcional
    })

    def essentials_ok(self) -> bool:
        """CSF, CURP, ACTA_NAC, INE son esenciales; COMP_DOMICILIO es opcional."""
        need = ["CSF", "CURP", "ACTA_NAC", "INE"]
        return all(self.paths.get(k) for k in need)
