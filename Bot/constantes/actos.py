#Imports independientes
import re
from typing import List, Dict

#Imports mios
from Bot.constantes.papeleria import *

REGEX_POR_ACTO: Dict[str, List[str]] = {
    "ACLARACION O RECTIFICACION": [re.compile(r"^(aclaraci[oó]n|rectificaci[óo]n).*", re.IGNORECASE)],#( aclaraci(o|ó) | rectificaci(o|ó)n )
    "ADJUDICACION JUDICIAL (HERENCIA)": [re.compile(r"^(adjudicaci[óo]n\s+(.*)?(her.*))", re.IGNORECASE)],#adjuciaci(o|ó)n her...
    "ADJUDICACION JUDICIAL": [re.compile(r"^(adjudicaci[óo]n).*", re.IGNORECASE)],#adjuciaci(o|ó)n
    "AFP / CARTA PERMISO MENOR DE EDAD": [re.compile(r"^(carta\s+(de\s+)?permiso).*", re.IGNORECASE)],#carta (de) permiso
    "AFP / EXTRAVIO DE DOCUMENTACION": [re.compile(r"^(extravio\s*(de\s+)?(doc.*)?).*", re.IGNORECASE)],#estravio (de)? doc...
    "AFP / FE DE HECHOS": [re.compile(r"^f[eé](\s+de)?\s+hechos", re.IGNORECASE)],#f(é|e) (de)? hecho(s)?
    "AFP / OFICIOS SUCESION": [re.compile(r"^(oficios).*", re.IGNORECASE)],#oficios suc...
    "AFP / PODER RATIFICADO": [re.compile(r"^(poder\s+rat(.*)?)", re.IGNORECASE)],#poder rat...
    "AFP / TESTIMONIAL VEHICULAR (FACTURA)": [re.compile(r"^(testimoni(o|al)\s+veh.*)", re.IGNORECASE)],#testimoni(o|al) veh...
    "AFP/CONCUBINATO": [re.compile(r"^(concubin.*)", re.IGNORECASE)],#concubin...
    "AFP/RATIFICACIÓN DE FIRMAS": [re.compile(r"^(ratificaci[o|ó]n\s*(de\s+)?(fir.*)?).*", re.IGNORECASE)],#ratificacion fir...
    "APERTURA DE CREDITO": [re.compile(r"^(apertura\s*+(de\s+)?(cr[é|e]d.*)?).*", re.IGNORECASE)],#apertura cred...
    "APORTACION A FIDEICOMISO": [re.compile(r"^aportaci[oó]n\s*a?(fideicomiso)?.*", re.IGNORECASE)],
    "CANCELACIÓN DE HIPOTECA": [re.compile(r"^(cancelaci[oó]n|canc)\s+(de\s+)?hip.*", re.IGNORECASE)],
    "CANCELACIÓN DE RESERVA DE DOMINIO": [re.compile(r"^(cancelaci[oó]n|canc)\s+(de\s+)?(res.*|dom.*)", re.IGNORECASE)],
    "CANCELACION DE USUFRUCTO VITALICIO": [re.compile(r"^(cancelaci[oó]n|canc)\s+(de\s+)?(usuf.*\svit.*|vit.*)", re.IGNORECASE)],
    "CANCELACION DE USUFRUCTO": [re.compile(r"^(cancelaci[oó]n|canc)\s+(de\s+)?usuf.*", re.IGNORECASE)],
    "CANCELACION PARCIAL DE HIPOTECA": [re.compile(r"^(cancelaci[oó]n|canc)\s+parcial.*", re.IGNORECASE)],
    "CAPITULACIONES MATRIMONIALES": [re.compile(r"^capitulaciones(\s+mat.*)?", re.IGNORECASE)],
    "COMPRAVENTA CON APERTURA DE CREDITO CON BANCO": [re.compile(r"^(compraventa|cv)\s+(banco|apertura|(cr[eé]dito|cr[eé]d)).*", re.IGNORECASE)],
    "COMPRAVENTA INFONAVIT": [re.compile(r"^(compraventa|cv)\s+infonavit", re.IGNORECASE)],
    "COMPRAVENTA FOVISSSTE": [re.compile(r"^(compraventa|cv)\s+fovis{1,3}te", re.IGNORECASE)],
    "COMPRAVENTA": [re.compile(r"^compraventa.*|cv.*", re.IGNORECASE)],
    "CONSTITUCIÓN DE ASOCIACIONES Y SOCIEDADES CIVILES": [re.compile(r"^constituci[oó]n\s+(de\s+)?(asoc.*|soc.* civ.*)", re.IGNORECASE)],#Consitucion de asoc|constitucion sociedades civiles|constitucion soc civ
    "CONSTITUCION DE PATRIMONIO FAMILIAR": [re.compile(r"^constituci[oó]n\s+(de\s+)?patr.*", re.IGNORECASE)],#Constitucion de patrimonio familiar|constitucion patrimonio
    "CONSTITUCIÓN DE SOCIEDADES MERCANTILES": [re.compile(r"^constituci[oó]n\s+(de\s+)?(soc.*)?merc.*", re.IGNORECASE)],#constitucion de sociedades mercantiles|constitucion mercantiles
    "CONVENIO MODIFICATORIO": [re.compile(r"^convenio.*", re.IGNORECASE)],#Convenio...
    "DACION EN PAGO": [re.compile(r"^daci[oó]n.*", re.IGNORECASE)],#Dacion...
    "DECLARACION DE HEREDEROS": [re.compile(r"^declaraci[oó]n.*", re.IGNORECASE)],#Declaracion...
    "DILIGENCIAS DE JURISDICCIÓN VOLUNTARIA": [re.compile(r"^(diligencias|jurisdicci[oó]n).*", re.IGNORECASE)],#Diligencias...|Jurisdiccion...
    "DONACION DE DINERO": [re.compile(r"^donaci[oó]n\s+(de\s+)?dinero.*", re.IGNORECASE)],#Donacion dinero|Donacion de dinero
    "DONACIÓN": [re.compile(r"^donaci[oó]n.*", re.IGNORECASE)],#Donacion...
    "EXTINCIÓN DE PATRIMONIO FAMILIAR CONCLUSIÓN": [re.compile(r"^extinci[oó]n\s+(de\s+)?patr.*", re.IGNORECASE)],#Extincion de patrimonio|Extincion patr.
    "FIDEICOMISO": [re.compile(r"^fideicomiso.*", re.IGNORECASE)],#Fideicomiso...
    "INVENTARIO Y AVALUO SUCESION": [re.compile(r"^inventario.*", re.IGNORECASE)],#Inventario...
    "PERMUTA": [re.compile(r"^permuta.*", re.IGNORECASE)],#Permuta...
    "PODER O MANDATO": [re.compile(r"^(poder|mandato).*", re.IGNORECASE)],#Poder...|Mandato...
    "PROTOCOLIZACION CONDOMINIO O FRACCIONAMIENTO": [re.compile(r"^(protocolizaci[oó]n|prot.*)\s+(cond.*|frac.*)", re.IGNORECASE)],#Protocolizacion condominio | Prot fraccionamiento
    "PROTOCOLIZACION DE ACTA DE ASAMBLEA": [re.compile(r"^(protocolizaci[oó]n|prot.*)\s+(de\s+)?(acta|asam.*)", re.IGNORECASE)],#Protocolizacion de acta | Prot asamblea
    "PROTOCOLIZACION DE ADECUACION DE SUPERFICIE": [re.compile(r"^(protocolizaci[oó]n|prot.*)\s+(de\s+)?(adec.*|sup.*)", re.IGNORECASE)],#Protocolizacion de superficie | Prot adecuacion
    "PROTOCOLIZACION DE CESION DE DERECHOS": [re.compile(r"^(protocolizaci[oó]n|prot.*)\s+(de\s+)?(ces.*|der.*)", re.IGNORECASE)],#Protocolizacion de cesion de derechos | Prot de cesion
    "PROTOCOLIZACION DE CONTRATO EN GENERAL": [re.compile(r"^(protocolizaci[oó]n|prot.*)\s+(de\s+)?(cont.*|gen.*)", re.IGNORECASE)],#Protocolizacion de contrato general | Prot general
    "PROTOCOLIZACIÓN DE OFICIO DE FUSIÓN, SUBDIVISIÓN, RELOTIFICACION Y/O LOTIFICAICON; CON DIVISION DE LA COSA COMUN": [re.compile(r"^(protocolizaci[oó]n|prot.*)\s+(de\s+)?(ofic.*)?(fus|subd|relot|lotif).*com[uú]n", re.IGNORECASE)],#Protocolizacion fusion comun | Prot de oficio de subdivision comun
    "PROTOCOLIZACIÓN DE OFICIO DE FUSIÓN, SUBDIVISIÓN, RELOTIFICACION Y/O LOTIFICAICON": [re.compile(r"^(protocolizaci[oó]n|prot.*)\s+(de\s+)?(ofic.*)?(fus|subd|relot|lotif).*", re.IGNORECASE)],#Protocolizacion fusion | Prot de oficio de subdivision
    "PROTOCOLIZACION DE SENTENCIA DE DIVORCIO": [re.compile(r"^(protocolizaci[oó]n|prot.*)\s+(de\s+)?(sent|div).*", re.IGNORECASE)],#Protocolizacion de sentencia | Prot divorcio
    "RECONOCIMIENTO DE ADEUDO (CONSTITUCION DE HIPOTECA)": [re.compile(r"^reconocimiento.*", re.IGNORECASE)],#Reconocimiento...
    "REDENCIÓN PASIVOS CON MUTUO DE FOVISSSTE": [re.compile(r"^redenci[óo]n", re.IGNORECASE)],#|Redencion...
    "REVOCACIÓN DE PODER": [re.compile(r"^revocaci[oó]", re.IGNORECASE)],#Revocacion...
    "TESTAMENTO": [re.compile(r"^testamento", re.IGNORECASE)],#Testamento...
    "TRANSMISIÓN DE PROPIEDAD Y EJECUCIÓN Y EXTINCIÓN PARCIAL DE FIDEICOMISO": [re.compile(r"^trans.*(ejec|extin|parc|fidei).*", re.IGNORECASE)],#Transmision parcial de fideicomiso | Trans fideicomiso
    "TRANSMISION DE PROPIEDAD": [re.compile(r"^trans.* prop.*", re.IGNORECASE)],#Transmision de propiedad | Transm prop
 }

ALIAS_POR_ACTO: Dict[str, List[str]] = {
    "ACLARACION O RECTIFICACION": ["aclaracion","rectificacion","rectificación","rectifica","rectificacion datos","aclaracion de"],
    "ADJUDICACION JUDICIAL": ["adjudicacion","adjudicación"],
    "ADJUDICACIÓN JUDICIAL (HERENCIA)": ["adjudicacion herencia","adjudicación herencia","adj herencia"],
    "AFP / CARTA PERMISO MENOR DE EDAD": ["carta permiso","carta de permiso","carta permiso menor","permiso menor","permiso menor de edad","permiso hijo","permiso hija","permiso hij@","permiso hijo menor","carta permiso hijo","carta permiso hija"],
    "AFP / EXTRAVIO DE DOCUMENTACION": ["extravío","extravío docs","extravio","extravio documentacion", "extravio de documentacion"],
    "AFP / FE DE HECHOS": ["fe de hechos","fe hechos"],
    "AFP / OFICIOS SUCESION": ["oficios","oficios sucesion","oficio sucesion"],
    "AFP / PODER RATIFICADO": ["poder ratificado","ratificar poder"],
    "AFP / TESTIMONIAL VEHICULAR (FACTURA)": ["testimonial vehicular","testimonial vehicular factura","testimonioal vehicular"],
    "AFP/CONCUBINATO": ["concubinato"],
    "AFP/RATIFICACIÓN DE FIRMAS": ["ratificacion firmas","ratificación firmas","rat de firmas","rat firmas"],
    "APERTURA DE CREDITO": ["apertura credito","ap credito","ap. credito","apertura crédito"],
    "APORTACION A FIDEICOMISO": ["aportacion fideicomiso","ap a fideicomiso","ap fideicomiso"],
    "CANCELACIÓN DE HIPOTECA": ["cancelacion hipoteca","cancel hipoteca","canc hipoteca"],
    "CANCELACIÓN DE RESERVA DE DOMINIO": ["cancelacion dominio","cancelación dominio"],
    "CANCELACION DE USUFRUCTO": ["cancelacion usufructo", "cancelacion de usufructo"],
    "CANCELACION DE USUFRUCTO VITALICIO": ["cancelacion usufructo vit","cancelación usufructo vitalicio"],
    "CANCELACION PARCIAL DE HIPOTECA": ["cancelacion parcial hip","cancelacion parcial hipoteca","canc parcial hipoteca"],
    "CAPITULACIONES MATRIMONIALES": ["capitulaciones patrimoniales","capitulaciones"],
    "COMPRAVENTA": ["cv","compra venta","compra-venta","compravta","venta","esc compra venta", "compraventa"],
    "COMPRAVENTA CON APERTURA DE CREDITO CON BANCO": ["compraventa apertura credito","cv apertura credito","apertura credito banco","compra-venta con apertura de credito","cv ap credito banco","credito bancario","compraventa apertura crédito","compraventa con apertura crédito"],
    "COMPRAVENTA INFONAVIT": ["cv infonavit","compra venta infonavit","infonavit compra venta","infonavit cv","compraventa infonavit"],
    "COMPRAVENTA FOVISSSTE": ["cv fovis","cv fovissste","compra venta fovis","fovissste compra venta","fovis cv","compraventa fovissste"],
    "CONSTITUCIÓN DE ASOCIACIONES Y SOCIEDADES CIVILES": ["constitución sociedades civiles","constitucion sociedades civiles","constitucion asociaciones civiles"],
    "CONSTITUCION DE PATRIMONIO FAMILIAR": ["constitucion patrimonio","constitución patrimonio familiar"],
    "CONSTITUCIÓN DE SOCIEDADES MERCANTILES": ["constitucion sociedades mercantiles","constitución sociedades mercantiles"],
    "CONVENIO MODIFICATORIO": ["convenio modificatorio","convenio modif"],
    "DACION EN PAGO": ["dacion en pago","dación en pago","dacion"],
    "DECLARACION DE HEREDEROS": ["declaracion de herederos","declaración de herederos"],
    "DILIGENCIAS DE JURISDICCIÓN VOLUNTARIA": ["diligencias","jurisdiccion voluntaria","jurisdicción voluntaria"],
    "DONACIÓN": ["donacion"],
    "DONACION DE DINERO": ["donacion de dinero","donación de dinero"],
    "EXTINCIÓN DE PATRIMONIO FAMILIAR CONCLUSIÓN": ["extincion patrimonio","extinción patrimonio familiar"],
    "FIDEICOMISO": ["fideicomiso"],
    "INVENTARIO Y AVALUO SUCESION": ["inventario y avaluo","inventario y avalúo","inventario avaluo sucesion"],
    "PERMUTA": ["permuta", "perm", "perm."],
    "PODER O MANDATO": ["poder","mandato","otorgamiento de poder"],
    "PROTOCOLIZACION CONDOMINIO O FRACCIONAMIENTO": ["pr condominio","pr fraccionamiento","pr fracc","pr cond","protoc condominio","protoc fraccionamiento"],
    "PROTOCOLIZACION DE ACTA DE ASAMBLEA": ["pr acta de asamblea","protocolizacion acta asamblea","prot acta asamblea"],
    "PROTOCOLIZACION DE ADECUACION DE SUPERFICIE": ["pr adecuacion","pr adecuación","protocolizacion adecuacion superficie"],
    "PROTOCOLIZACION DE CESION DE DERECHOS": ["pr cesion de derechos","protocolizacion cesion de derechos"],
    "PROTOCOLIZACION DE CONTRATO EN GENERAL": ["pr contrato gral","protocolizacion contrato general","pr contrato general"],
    "PROTOCOLIZACIÓN DE OFICIO DE FUSIÓN, SUBDIVISIÓN, RELOTIFICACION Y/O LOTIFICAICON": ["pr oficio de fusion","pr subdivision","pr relotificacion","pr lotificacion","protocolizacion oficio fusion","protocolizacion oficio subdivision","protocolizacion oficio relotificacion","protocolizacion oficio lotificacion"],
    "PROTOCOLIZACIÓN DE OFICIO DE FUSIÓN, SUBDIVISIÓN, RELOTIFICACION Y/O LOTIFICAICON; CON DIVISION DE LA COSA COMUN": ["pr oficio de fusion comun","pr subdivision comun","pr relotificacion comun","pr lotificacion comun"],
    "PROTOCOLIZACION DE SENTENCIA DE DIVORCIO": ["pr sentencia de divorcio","protocolizacion sentencia divorcio","prot sentencia divorcio"],
    "RECONOCIMIENTO DE ADEUDO (CONSTITUCION DE HIPOTECA)": ["reconomiento adeudo","reconocimiento adeudo","constitucion hipoteca","rcn adeudo"],
    "REDENCIÓN PASIVOS CON MUTUO DE FOVISSSTE": ["redencion pasivos","redención pasivos fovissste","redencion fovis"],
    "REVOCACIÓN DE PODER": ["revocacion de poder","revocar poder"],
    "TESTAMENTO": ["testamento"],
    "TRANSMISION DE PROPIEDAD": ["transmision de propiedad","transmisión de propiedad"],
    "TRANSMISIÓN DE PROPIEDAD Y EJECUCIÓN Y EXTINCIÓN PARCIAL DE FIDEICOMISO": ["transmision de propiedad fideicomiso","transmision propiedad y ejecucion fideicomiso","transmisión de propiedad fideicomiso"],
}

ROLES_POR_ACTO = {

        "ACLARACION O RECTIFICACION": [
            "compareciente",
        ],

        "ADJUDICACION JUDICIAL": [
            "adquiriente",
            "enajenante",
            "juez",
            "secretario",
        ],

        "ADJUDICACIÓN JUDICIAL (HERENCIA)": [
            "adquiriente",
            "enajenante",
            "juez",
            "secretario en rebeldía",
        ],

        "AFP / CARTA PERMISO MENOR DE EDAD": [
            "hij@",
            "madre",
            "padre",
        ],

        "AFP / EXTRAVIO DE DOCUMENTACION": [
            "compareciente",
        ],

        "AFP / FE DE HECHOS": [
            "compareciente 1",
            "compareciente 2",
        ],

        "AFP / OFICIOS SUCESION": [
            "compareciente",
        ],

        "AFP / PODER RATIFICADO": [
            "poderdante",
        ],

        "AFP / TESTIMONIAL VEHICULAR (FACTURA)": [
            "dueño vehiculo",
            "testigo 1",
            "testigo 2",
        ],

        "AFP/CONCUBINATO": [
            "concubino 1",
            "concubino 2",
        ],

        "AFP/RATIFICACIÓN DE FIRMAS": [
            "compareciente",
        ],

        "APERTURA DE CREDITO": [
            "acreditado",
            "acreditante",
        ],

        "APORTACION A FIDEICOMISO": [
            "depositario",
            "fideicomisario",
            "fideicomitente",
            "fiduciario",
        ],

        "CANCELACIÓN DE HIPOTECA": [
            "acreedor",
            "deudor",
        ],

        "CANCELACIÓN DE RESERVA DE DOMINIO": [
            "transmisora",
        ],

        "CANCELACION DE USUFRUCTO": [
            "nudo propietario",
            "usufructuario",
        ],

        "CANCELACION DE USUFRUCTO VITALICIO": [
            "nudo propiuetario",
            "usufructuario",
        ],

        "CANCELACION PARCIAL DE HIPOTECA": [
            "acreditado",
            "acreedor",
            "deudor",
        ],

        "CAPITULACIONES MATRIMONIALES": [
            "cónyugue 1",
            "cónyugue 2",
        ],

        "COMPRAVENTA": [
            "comprador",
            "vendedor",
            "apoderado",
        ],

        "COMPRAVENTA CON APERTURA DE CREDITO CON BANCO": [
            "banco",
            "comprador/acreditado",
            "vendedor",
            "Vendedor construccion",
            "vendedr terreno",
        ],

        "COMPRAVENTA FOVISSSTE": [
            "comprador/acreditado",
            "fovissste",
            "vendedor",
        ],

        "COMPRAVENTA INFONAVIT": [
            "comprador",
            "infonavit",
            "vendedor",
        ],

        "CONSTITUCIÓN DE ASOCIACIONES Y SOCIEDADES CIVILES": [
            "representante legal",
            "socios/accionistas",
        ],

        "CONSTITUCION DE PATRIMONIO FAMILIAR": [
            "compareciente",
        ],

        "CONSTITUCIÓN DE SOCIEDADES MERCANTILES": [
            "accionistas",
            "administrador",
            "comisario",
            "presidente",
            "secretario",
            "socios",
            "tesorero",
            "vocales",
        ],

        "CONVENIO MODIFICATORIO": [
            "compareciente 1",
            "compareciente 2",
            "compareciente 3",
        ],

        "DACION EN PAGO": [
            "acredor",
            "deudor",
        ],

        "DECLARACION DE HEREDEROS": [
            "albacea",
            "heredero",
        ],

        "DILIGENCIAS DE JURISDICCIÓN VOLUNTARIA": [
            "compareciente",
            "testigo",
        ],

        "DONACIÓN": [
            "donante",
            "donatario",
        ],

        "DONACION DE DINERO": [
            "donante",
            "donatario",
        ],

        "EXTINCIÓN DE PATRIMONIO FAMILIAR CONCLUSIÓN": [
            "compareciente",
        ],

        "FIDEICOMISO": [
            "fideicomisario",
            "fideicomitente",
            "fiduciario",
        ],

        "INVENTARIO Y AVALUO SUCESION": [
            "comparecientes",
        ],

        "PERMUTA": [
            "permutante A",
            "permutante B",
        ],

        "PODER O MANDATO": [
            "apoderado",
            "poderdante",
        ],

        "PROTOCOLIZACION CONDOMINIO O FRACCIONAMIENTO": [
            "compareciente",
            "fraccionador",
            "presidente municipal",
            "secretario municipal",
        ],

        "PROTOCOLIZACION DE ACTA DE ASAMBLEA": [
            "delegado especial",
            "nombre sociedad",
        ],

        "PROTOCOLIZACION DE ADECUACION DE SUPERFICIE": [
            "cliente",
        ],

        "PROTOCOLIZACION DE CESION DE DERECHOS": [
            "cedente",
            "cesionario",
        ],

        "PROTOCOLIZACION DE CONTRATO EN GENERAL": [
            "parte 1",
            "parte 2",
            "parte 3",
        ],

        "PROTOCOLIZACIÓN DE OFICIO DE FUSIÓN, SUBDIVISIÓN, RELOTIFICAICON Y/O LOTIFICACION": [
            "compareciente",
        ],

        "PROTOCOLIZACIÓN DE OFICIO DE FUSIÓN, SUBDIVISIÓN, RELOTIFICAICON Y/O LOTIFICACION; CON DIVISION DE LA COSA COMUN": [
            "compareciente",
        ],

        "PROTOCOLIZACION DE SENTENCIA DE DIVORCIO": [
            "adquiriente",
            "transmisor",
        ],

        "RECONOCIMIENTO DE ADEUDO (CONSTITUCION DE HIPOTECA)": [
            "acreditado",
            "acreedor",
        ],

        "REDENCIÓN PASIVOS CON MUTUO DE FOVISSSTE": [
            "mutuante",
            "mutuario",
        ],

        "REVOCACIÓN DE PODER": [
            "apoderado",
            "poderdante",
        ],

        "TESTAMENTO": [
            "testador",
            "testigo",
        ],

        "TRANSMISION DE PROPIEDAD": [
            "adquiriente",
            "enajenante",
        ],

        "TRANSMISIÓN DE PROPIEDAD Y EJECUCIÓN Y EXTINCIÓN PARCIAL DE FIDEICOMISO": [
            "adquiriente",
            "delegado fiduciario",
            "depositario",
            "fideicomitente o Fideicomisario",
            "fiduciario",
            "representante Legal",
        ],
    }

GRUPO_ACTOS = {
    'CV_ADJ_DON': [re.compile(r"(donaci[óo]n|compraventa|adjudicaci[oó]n)", re.IGNORECASE)],
    'PODERES': [re.compile(r"poder", re.IGNORECASE)],
    'APERTURAS_CREDITO':[re.compile(r"cr[eé]dito", re.IGNORECASE)],
    'CANCELACION_HIPOTECA': [re.compile(r"cancelaci[oó]n.*hipoteca]", re.IGNORECASE)],
    'TESTAMENTO': [re.compile(r"testamento", re.IGNORECASE)],
    'ASAMBLEAS': [re.compile(r"asamblea", re.IGNORECASE)],
    'CONSTITUTIVAS': [re.compile(r"constituci[oó]n.*sociedades", re.IGNORECASE)],
}

PAPALERIA_POR_GRUPO = {
    'PERSONA_FISICA': [INE,CURP, CSF,ACTA_NAC],
    'PERSONA_MORAL': [CSF_SOCIEDAD, ASAMBLEAS],
    'CV_ADJ_DON': [PAGO_PREDIAL, ESCRITURA_ANTECEDENTE, CLG, AVALUO_CATASTRAL, AVALUO_REFERIDO, AVALUO_COMERCIAL, SOLICITUD_AVALUO],
    'PODERES': [TITULO_PROPIEDAD],
    'APERTURAS_CREDITO': [ESCRITURA_ANTECEDENTE, CLG,SOLICITUD_AVALUO,AVALUO_CATASTRAL,AVALUO_COMERCIAL,AVALUO_REFERIDO, CARTA_INSTRUCCION],
    'CANCELACION_HIPOTECA': [CLG,CARTA_INSTRUCCION],
    'TESTAMENTO': [ESCRITURA_ANTECEDENTE],
    'ASAMBLEAS': [ASAMBLEA_A_PROTOCOLIZAR],
    'CONSTITUTIVAS': [PROPUESTAS_NOMBRES]
}