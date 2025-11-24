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

    def get(self, doc: str) -> str:
        if doc == "CSF": return self.CSF
        elif doc == "CURP": return self.CURP        
        elif doc == "ACTA_NAC": return self.ACTA_NAC
        elif doc == "INE": return self.INE
        elif doc == "ACTA_MATRIMONIO": return self.ACTA_MATRIMONIO
        elif doc == "COMP_DOMICILIO": return self.COMP_DOMICILIO
        else: return None;


@dataclass
class Persona:
    nombre: Optional[str] = None
    rfc: Optional[str] = None
    idcif: Optional[str] = None
    docs: DocumentoPaths = field(default_factory=DocumentoPaths)
    uif: str = None  # Ruta al documento UIF

    def get(self, data:str):
        if data == "nombre": return self.nombre
        elif data == "rfc": return self.rfc
        elif data == "idcif": return self.idcif
        elif data == "docs": return self.docs

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

    # Documentos de banco (solo si es_banco = True)
    es_banco: bool = False
    carta_instruccion: Optional[str] = None   
    uif: str = None

@dataclass
class Inmueble:
    nombre: str
    docs: Dict[str, Optional[str]] = field(default_factory=dict)

    def get_name(self) -> str:
        return self.nombre

    def get(self, doc: str) -> str:
        if doc == "Escritura Antecedente (Inmueble)": return self.docs["ESCRITURA_ANTECEDENTE"]
        elif doc == "Recibo de pago del impuesto predial": return self.docs["RECIBO_PREDIAL"]
        elif doc == "Avalúo Catastral": return self.docs["AVALUO_CATASTRAL"]
        elif doc == "Aviso preventivo": return self.docs["AVISO_PREVENTIVO"]
        elif doc == "Solicitud de Avalúo": return self.docs["SOLICITUD_AVALUO"]
        elif doc == "Plano": return self.docs["PLANO"]
        else: return None


@dataclass
class ActoExtraction:
    acto_nombre: str
    partes_pf: List[PersonaFisica] = field(default_factory=list)
    partes_pm: List[Sociedad] = field(default_factory=list)
    inmuebles: List[Inmueble] = field(default_factory=list)
    otros: List[str] = field(default_factory=list)
    # NUEVOS CAMPOS
    cliente_principal: Optional[str] = None
    cliente_fuente: Optional[str] = None  # "partes" o "carpeta"
    escritura: Optional[int] = None       # <== NUEVO

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
                        "UIF": "",
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
                        "UIF": "",
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
                },
                "es_banco": pm.es_banco,
                "CARTA_INSTRUCCION": pm.docs.carta_instruccion,
                "UIF": "",
            }

        return {
            "acto_nombre": self.acto_nombre,
            "cliente_principal": self.cliente_principal,
            "cliente_fuente": self.cliente_fuente,
            "escritura": self.escritura,
            "partes_pf": [_pf(x) for x in self.partes_pf],
            "partes_pm": [_pm(x) for x in self.partes_pm],
            "inmuebles": [{"nombre": i.nombre, "docs": i.docs} for i in self.inmuebles],
            "otros": self.otros,
        }