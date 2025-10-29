from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

# Contenedor de rutas típicas para personas / sociedades
@dataclass
class DocumentoPaths:
    CSF: Optional[str] = None
    CURP: Optional[str] = None
    ACTA_NAC: Optional[str] = None
    INE: Optional[str] = None
    COMP_DOMICILIO: Optional[str] = None
    ACTA_MATRIMONIO: Optional[str] = None

    # Sociedad
    CSF_SOCIEDAD: Optional[str] = None
    ACTA_CONSTITUTIVA: Optional[str] = None
    PODER_REPRESENTANTE: Optional[str] = None
    ASAMBLEAS: List[str] = field(default_factory=list)
    OTROS: List[str] = field(default_factory=list)

@dataclass
class Persona:
    nombre: Optional[str] = None
    rfc: Optional[str] = None
    idcif: Optional[str] = None
    docs: DocumentoPaths = field(default_factory=DocumentoPaths)

@dataclass
class PersonaFisica:
    rol: str = ""
    persona: Persona = field(default_factory=Persona)
    esposa_o_esposo: Optional[Persona] = None

@dataclass
class Sociedad:
    rol: str = ""
    nombre: Optional[str] = None          # Razón social (forzada desde CSF)
    rfc: Optional[str] = None             # RFC de la sociedad (nuevo)
    idcif: Optional[str] = None           # idCIF de la sociedad (nuevo)
    representante: Optional[Persona] = None
    docs: DocumentoPaths = field(default_factory=DocumentoPaths)

@dataclass
class Inmueble:
    nombre: str
    docs: Dict[str, Optional[str]] = field(default_factory=dict)

@dataclass
class ActoExtraction:
    acto_nombre: str
    partes_pf: List[PersonaFisica] = field(default_factory=list)
    partes_pm: List[Sociedad] = field(default_factory=list)
    inmuebles: List[Inmueble] = field(default_factory=list)
    otros: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        def _pf(pf: PersonaFisica):
            return {
                "rol": pf.rol,
                "persona": {
                    "nombre": pf.persona.nombre,
                    "rfc": pf.persona.rfc,
                    "idcif": pf.persona.idcif,
                    "docs": {
                        "CSF": pf.persona.docs.CSF,
                        "CURP": pf.persona.docs.CURP,
                        "ACTA_NAC": pf.persona.docs.ACTA_NAC,
                        "INE": pf.persona.docs.INE,
                        "COMP_DOMICILIO": pf.persona.docs.COMP_DOMICILIO,
                        "ACTA_MATRIMONIO": pf.persona.docs.ACTA_MATRIMONIO,
                    }
                },
                "esposa_o_esposo": None if not pf.esposa_o_esposo else {
                    "nombre": pf.esposa_o_esposo.nombre,
                    "rfc": pf.esposa_o_esposo.rfc,
                    "idcif": pf.esposa_o_esposo.idcif,
                    "docs": {
                        "CSF": pf.esposa_o_esposo.docs.CSF,
                        "CURP": pf.esposa_o_esposo.docs.CURP,
                        "ACTA_NAC": pf.esposa_o_esposo.docs.ACTA_NAC,
                        "INE": pf.esposa_o_esposo.docs.INE,
                        "COMP_DOMICILIO": pf.esposa_o_esposo.docs.COMP_DOMICILIO,
                        "ACTA_MATRIMONIO": pf.esposa_o_esposo.docs.ACTA_MATRIMONIO,
                    }
                }
            }

        def _pm(pm: Sociedad):
            return {
                "rol": pm.rol,
                "nombre": pm.nombre,
                "rfc": pm.rfc,
                "idcif": pm.idcif,
                "representante": None if not pm.representante else {
                    "nombre": pm.representante.nombre,
                    "rfc": pm.representante.rfc,
                    "idcif": pm.representante.idcif,
                    "docs": {
                        "CSF": pm.representante.docs.CSF,
                        "CURP": pm.representante.docs.CURP,
                        "ACTA_NAC": pm.representante.docs.ACTA_NAC,
                        "INE": pm.representante.docs.INE,
                        "COMP_DOMICILIO": pm.representante.docs.COMP_DOMICILIO,
                        "ACTA_MATRIMONIO": pm.representante.docs.ACTA_MATRIMONIO,
                    }
                },
                "docs": {
                    "CSF_SOCIEDAD": pm.docs.CSF_SOCIEDAD,
                    "ACTA_CONSTITUTIVA": pm.docs.ACTA_CONSTITUTIVA,
                    "PODER_REPRESENTANTE": pm.docs.PODER_REPRESENTANTE,
                    "ASAMBLEAS": pm.docs.ASAMBLEAS,
                    "OTROS": pm.docs.OTROS,
                }
            }

        return {
            "acto_nombre": self.acto_nombre,
            "partes_pf": [_pf(x) for x in self.partes_pf],
            "partes_pm": [_pm(x) for x in self.partes_pm],
            "inmuebles": [{"nombre": i.nombre, "docs": i.docs} for i in self.inmuebles],
            "otros": self.otros,
        }
