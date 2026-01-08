#Imports mios
from Bot.models.modelos import Proyecto
from Bot.config.actos import PAPALERIA_POR_GRUPO, GRUPO_ACTOS
from Bot.config.papeleria import LISTA_UIF1, LISTA_UIF2

def papeleria_importante(proyecto: Proyecto) -> list:
    papeleria_total = []
    for acto in proyecto.actos_involucrados:
        for grupo, regexs in GRUPO_ACTOS.items():
            for regex in regexs:
                if regex.search(acto):
                    papeleria_total.extend(PAPALERIA_POR_GRUPO.get(grupo, []))
                    break
    if len(proyecto.pfs)>0:
        papeleria_total.extend(PAPALERIA_POR_GRUPO.get('PERSONA_FISICA',[]))
    if len(proyecto.pms)>0:
        papeleria_total.extend(PAPALERIA_POR_GRUPO.get('PERSONA_MORAL',[]))
    
    papeleria_total.extend([LISTA_UIF1, LISTA_UIF2])
    return list(set(papeleria_total))
