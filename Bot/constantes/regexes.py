import re

#Docs persona fisica
CSF_R = [
    re.compile(r"csf.*", re.IGNORECASE),
    re.compile(r"constancia\s+de\s+situacion\s+fiscal", re.IGNORECASE),
    re.compile(r"cedula\s+de\s+identificacion\s+fiscal", re.IGNORECASE),
    re.compile(r"\bcedula\s+fiscal\b", re.IGNORECASE),
]
CURP_R = [re.compile(r"\bcurp\b", re.IGNORECASE)]
ACTA_NAC_R = [
            re.compile(r"\bacta\s+de\s+nacimiento\b", re.IGNORECASE),
            re.compile(r"\bacta\s+nacimiento\b", re.IGNORECASE),
            re.compile(r"\bacta[_\- ]*nac\b", re.IGNORECASE),
            re.compile(r"\bactanac\b", re.IGNORECASE),
        ]
COMPROBANTE_DOMICILIO_R = [
            re.compile(r"\bcomprobante\s+de\s+domicilio\b",re.IGNORECASE),
            re.compile(r"\bcomp[_\- ]*dom\b",re.IGNORECASE),
            re.compile(r"\bcompdom\b",re.IGNORECASE),
        ]
ACTA_MATRIMONIO_R = [
            re.compile(r"\bacta\s+de\s+matrimonio\b", re.IGNORECASE),
            re.compile(r"\bacta\s+matrimonio\b", re.IGNORECASE),
        ]
INE_R = [
    re.compile(r"\bine\b", re.IGNORECASE),
    re.compile(r"\bife\b", re.IGNORECASE),
    re.compile(r"\bidentificacion\b", re.IGNORECASE),
    re.compile(r"\bidentificacion\s+oficial\b", re.IGNORECASE),
]

#Docs sociedad
ACTA_CONSTITUTIVA_R = [
            re.compile(r"\bacta\s+constitutiva\b", re.IGNORECASE),
            re.compile(r"\bconstitutiva\b", re.IGNORECASE),
        ]
PODER_REPRESENTANTE_LEGAL_R = [
            re.compile(r"\bpoder\b", re.IGNORECASE),
            re.compile(r"\bpoder\s+del\s+representante\b", re.IGNORECASE),
            re.compile(r"\bpoder\s+notarial\b", re.IGNORECASE),
        ]
ASAMBLEA_R = [
        re.compile(r"\basamblea\b", re.IGNORECASE),
        re.compile(r"\basambleas\b", re.IGNORECASE),
        re.compile(r"\bacta\s+de\s+asamblea\b", re.IGNORECASE),
    ]
ASAMBLEA_A_PROTOCOLIZAR_R = [
    re.compile(r"^(asamblea.*prot|asam.*prot)", re.IGNORECASE),
]
CARTA_INSTRUCCION_R = [
            re.compile(r"\bcarta\b", re.IGNORECASE),
            re.compile(r"\binstruccion\b", re.IGNORECASE),
            re.compile(r"\bcarta\s+de\s+instruccion\b", re.IGNORECASE),
        ]

#Inmuebles
ESCRITURA_ANTECEDENTE_R = [
            re.compile(r"\bantecedente\b", re.IGNORECASE),
            re.compile(r"\bEsc.\s+(de\s+)?antecedente\b", re.IGNORECASE),
            re.compile(r"\bescritura\s+(de\s+)?antecedente\b", re.IGNORECASE),
            re.compile(r"\bescritura\s+antecedente\b", re.IGNORECASE),
            re.compile(r"\bantecedente\s+escritura\b", re.IGNORECASE),
            re.compile(r"^Escritura.*", re.IGNORECASE),
        ]
CLG_R = [
        re.compile(r"\bcertificado\s+de\s+libertad\s+y?\s*gravamen",re.IGNORECASE),
        re.compile(r"\blibertad\s+y?\s*gravamen\b",re.IGNORECASE),
        re.compile(r"\bcert[_\- ]*libertad\b",re.IGNORECASE),
    ]
AVALUO_CATASTRAL_R = [re.compile(r"\bavaluo\s+catastral\b", re.IGNORECASE)]
AVALUO_COMERCIAL_R = [re.compile(r"\bavaluo\s+comercial\b", re.IGNORECASE)]
AVALUO_REFERIDO_R = [re.compile(r"\bavaluo\s+referido\b", re.IGNORECASE)]
AVISO_PREVENTIVO_R = [re.compile(r"\baviso\s+preventivo\b", re.IGNORECASE)]
SOLICITUD_AVALUO_R = [re.compile(r"\bsolicitud\s+de\s+avaluo\b",re.IGNORECASE), re.compile(r"\bsolicitud\s+avaluo\b", re.IGNORECASE)]
PLANO_R = [re.compile(r"\bplano\b",re.IGNORECASE), re.compile(r"\bplano\s+autorizado\b", re.IGNORECASE)]
PREDIAL_R = [re.compile(r"\b(recibo|pago)\s+predial\b",re.IGNORECASE), re.compile(r"\bpredial\b", re.IGNORECASE)]
TITULO_PROPIEDAD_R = [re.compile(r"\btitulo\s+de\s+propiedad\b",re.IGNORECASE), re.compile(r"\btitulo\s+propiedad\b", re.IGNORECASE)]
NO_ADEUDO_AGUA_R = [re.compile(r"\bno\s+adeudo\s+agua\b",re.IGNORECASE), re.compile(r"\b(no\s+)?adeudo\s+agua\b", re.IGNORECASE)]

#OTROS
LISTA_NOMINAL_R = [re.compile(r"\blista\s+nominal\b", re.IGNORECASE)]
EXPEDIENTE_JUDICIAL_R = [re.compile(r"expediente\s*jud", re.IGNORECASE),re.compile(r"exp\s*jud", re.IGNORECASE)]
CONSTANCIA_PAGO_R = [re.compile(r"constancia\s*pago", re.IGNORECASE),re.compile(r"constancia de pago", re.IGNORECASE)]
FORMA_ISAI_AMARILLA_R = [re.compile(r"isai.*amarilla", re.IGNORECASE),re.compile(r"forma\s*amarilla", re.IGNORECASE),re.compile(r"forma\s*isai", re.IGNORECASE)]
RECIBO_PAGO_ISAI_R = [re.compile(r"pago\s*isai", re.IGNORECASE),re.compile(r"recibo\s*isai", re.IGNORECASE)]
RECIBO_PAGO_DERECHOS_REGISTRO_R = [re.compile(r"pago.*registro", re.IGNORECASE),re.compile(r"recibo.*derechos.*registro", re.IGNORECASE)]
ESCRITURA_ANTECEDENTE_CREDITO_R = [re.compile(r"escritura\s*ant", re.IGNORECASE),re.compile(r"escritura.*(credito|fidei|convenios)", re.IGNORECASE),re.compile(r"ant\s*(credito|fidei)", re.IGNORECASE),re.compile(r"fideicomiso\s*const", re.IGNORECASE)]
ACTA_NACIMIENTO_CONYUGE_R = [re.compile(r"acta.*nacimiento.*(cony|c[oó]nyu)", re.IGNORECASE)]
IDENTIFICACION_CONYUGE_R = [re.compile(r"(ine|ife|identificacion).*(cony|c[oó]nyu)", re.IGNORECASE)]
LISTA_NOMINAL_R = [re.compile(r"lista.*nominal", re.IGNORECASE)]
COMPROBANTE_DOMICILIO_CONYUGE_R = [re.compile(r"(comp.*dom)|(recibo.*(cfe|agua|luz)).*(cony|c[oó]nyu)", re.IGNORECASE)]
CURP_CONYUGE_R = [re.compile(r"curp.*(cony|c[oó]nyu)", re.IGNORECASE)]
PROPUESTAS_NOMBRES_R = [re.compile(r"^propuesta.*", re.IGNORECASE)]