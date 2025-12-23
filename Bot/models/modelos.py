from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from Bot.config.papeleria import *

@dataclass
class DocsPersonaFisica:
    CSF: Optional[str] = None
    CURP: Optional[str] = None
    ACTA_NAC: Optional[str] = None
    INE: Optional[str] = None
    COMP_DOMICILIO: Optional[str] = None
    ACTA_MATRIMONIO: Optional[str] = None
    UIF: Optional[str] = None

    def obtener_documento(self, doc: str) -> Optional[str]:
        if doc == ACTA_NAC: return self.ACTA_NAC
        elif doc == CSF: return self.CSF
        elif doc == INE: return self.INE
        elif doc == CURP: return self.CURP
        elif doc == COMPROBANTE_DOMICILIO: return self.COMP_DOMICILIO
        elif doc == ACTA_MAT: return self.ACTA_MATRIMONIO
        elif doc == LISTA_UIF1 or doc == LISTA_UIF2: return self.UIF
        else: return None


@dataclass
class DocsSociedad:
    CSF_SOCIEDAD: Optional[str] = None
    ACTA_CONSTITUTIVA: Optional[str] = None
    PODER_REPRESENTANTE: Optional[str] = None
    CARTA_INSTRUCCION: Optional[str] = None
    ASAMBLEAS: List[str] = field(default_factory=list)
    UIF: Optional[str] = None
    
    def obtener_documento(self, doc:str) -> Optional[str]:
        if doc == CSF_SOCIEDAD: return self.CSF_SOCIEDAD
        elif doc == ACTA_CONSTITUTIVA: return self.ACTA_CONSTITUTIVA
        elif doc == PODER_REPRESENTANTE: return self.PODER_REPRESENTANTE
        elif doc == CARTA_INSTRUCCION: return self.CARTA_INSTRUCCION
        elif doc == ASAMBLEAS: return self.ASAMBLEAS
        elif doc == LISTA_UIF1 or doc == LISTA_UIF2: return self.UIF
        else: return None
        

@dataclass
class Persona:
    tipo: Optional[str] = None
    nombre: Optional[str] = None
    nombre_s: Optional[str] = None
    primer_apellido: Optional[str] = None
    segundo_apellido: Optional[str] = ""
    rfc: Optional[str] = None
    idcif: Optional[str] = None
    acto_perteneciente: str = None
    rol: Optional[str] = None
    conyugue: Optional[Persona] = None
    unknown: bool = False
    docs: DocsPersonaFisica = field(default_factory=DocsPersonaFisica)
    ruta_guardado: Optional[str] = None

@dataclass
class Sociedad:
    tipo: Optional[str] = None
    nombre: Optional[str] = None
    rfc: Optional[str] = None
    idcif: Optional[str] = None  
    rol: str = ""
    acto_perteneciente: str = None
    representantes: List[Persona] = field(default_factory=list)
    es_banco: bool = False
    unknown: bool = False
    docs: DocsSociedad = field(default_factory=DocsSociedad)
    ruta_guardado: Optional[str] = None
    


@dataclass
class DocsInmuebles:
    escritura_antecedente: Optional[str] = None
    cert_lib_gravamen: Optional[str] = None
    avaluo_catastral: Optional[str] = None
    avaluo_comercial: Optional[str] = None
    avaluo_referido: Optional[str] = None
    aviso_preventivo: Optional[str] = None
    solicitud_avaluo: Optional[str] = None
    plano: Optional[str] = None
    recibo_predial: Optional[str] = None
    titulo_propiedad: Optional[str] = None
    no_adeudo_agua: Optional[str] = None
    lista_nominal: Optional[str] = None

    def obtener_documento(self, doc: str) -> Optional[str]:
        if doc == ESCRITURA_ANTECEDENTE: return self.escritura_antecedente
        elif doc == CLG: return self.cert_lib_gravamen
        elif doc == AVALUO_CATASTRAL: return self.avaluo_catastral
        elif doc == AVALUO_COMERCIAL: return self.avaluo_comercial
        elif doc == AVALUO_REFERIDO: return self.avaluo_referido
        elif doc == AVISO_PREVENTIVO: return self.aviso_preventivo
        elif doc == SOLICITUD_AVALUO: return self.solicitud_avaluo
        elif doc == PLANO: return self.plano
        elif doc == PAGO_PREDIAL: return self.recibo_predial
        elif doc == TITULO_PROPIEDAD: return self.titulo_propiedad
        elif doc == NO_ADEUDO_AGUA: return self.no_adeudo_agua
        elif doc == LISTA_NOMINAL: return self.lista_nominal
        else: return None

@dataclass
class Inmueble:
    nombre: Optional[str] = None
    docs: DocsInmuebles = field(default_factory=DocsInmuebles)
    ruta_guardado: Optional[str] = None
    

@dataclass
class DocsOtros:
    expediente_judicial: Optional[str] = None
    constancia_pago: Optional[str] = None
    forma_isai_amarilla: Optional[str] = None
    recibo_pago_isai: Optional[str] = None
    recibo_pago_derechos_registro: Optional[str] = None
    escritura_antecedente_credito: Optional[str] = None
    acta_nacimiento_conyuge: Optional[str] = None
    identificacion_conyuge: Optional[str] = None
    lista_nominal: Optional[str] = None
    comprobante_domicilio_conyuge: Optional[str] = None
    curp_conyuge: Optional[str] = None
    carta_instruccion: Optional[str] = None
    poder_representante: Optional[str] = None
    titulo_propiedad: Optional[str] = None
    no_adeudo_agua: Optional[str] = None
    plano: Optional[str] = None
    otros: List[str] = field(default_factory=list)

    def obtener_documento(self, doc: str) -> Optional[str]:
        if doc == EXPEDIENTE_JUDICIAL: return self.expediente_judicial
        elif doc == CONSTANCIA_PAGO: return self.constancia_pago
        elif doc == FORMA_ISAI: return self.forma_isai_amarilla
        elif doc == PAGO_ISAI: return self.recibo_pago_isai
        elif doc == PAGO_DERECHOS_REGISTRO: return self.recibo_pago_derechos_registro
        elif doc == ESCRITURA_APERTURA_CREDITO: return self.escritura_antecedente_credito
        elif doc == ACTA_NAC_CONYUGUE: return self.acta_nacimiento_conyuge
        elif doc == INE_CONYUGUE: return self.identificacion_conyuge
        elif doc == LISTA_NOMINAL: return self.lista_nominal
        elif doc == COMPROBANTE_DOMICILIO_CONYUGUE: return self.comprobante_domicilio_conyuge
        elif doc == CURP_CONYUGUE: return self.curp_conyuge
        elif doc == CARTA_INSTRUCCION: return self.carta_instruccion
        elif doc == PODER_REPRESENTANTE: return self.poder_representante
        elif doc == TITULO_PROPIEDAD: return self.titulo_propiedad
        elif doc == NO_ADEUDO_AGUA: return self.no_adeudo_agua
        elif doc == PLANO: return self.plano
        elif doc == OTROS: return self.otros
        
        else: return None
        

@dataclass
class Proyecto:
    ruta: Optional[str] = None
    abogado: Optional[str] = None
    acto_principal: Optional[str] = None
    fecha: Optional[str] = None
    cliente_principal: Optional[str] = None
    folio: Optional[str] = None
    escritura: Optional[str] = None
    descripcion: Optional[str] = None
    actos_involucrados: List[str] = field(default_factory=list)
    pfs: List[Persona] = field(default_factory=list)
    pms: List[Sociedad] = field(default_factory=list)
    inmuebles: List[Inmueble] = field(default_factory=list)
    otros: DocsOtros = field(default_factory=DocsOtros)

@dataclass 
class ProyectoMod:
    ruta: Optional[str] = None
    fecha: Optional[str] = None
    abogado: Optional[str] = None
    acto_principal: Optional[str] = None
    cliente_principal: Optional[str] = None
    folio: Optional[str] = None
    escritura: Optional[str] = None
    descripcion: Optional[str] = None
    contadores: Dict[str, int] = field(default_factory=dict)
    faltantes: Dict[str, List[str]] = field(default_factory=dict)
    faltantes_nuevos: Dict[str, List[str]] = field(default_factory=dict)
    archivos_para_subir: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)