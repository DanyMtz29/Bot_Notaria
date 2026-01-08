#imports independientes
import os, json, ast
import pandas as pd
from dataclasses import asdict
from datetime import datetime, date

#imports mios
from Bot.models.modelos import Proyecto
from Bot.constantes.rutas import ARCHIVO_FALTANTES, MINIMO_DE_DIAS
from Bot.helpers.logs import registrar_log
from Bot.models.modelos import ProyectoMod
from Bot.helpers.carpetas import buscar_archivos_faltantes_pf, buscar_archivos_faltantes_pm, buscar_archivos_faltantes_inmueble

def leer_json(ruta_archivo: str) -> dict:
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        datos = json.load(archivo)
        return datos

def parsear(proyecto_a_modificar: ProyectoMod, key, val) -> bool:
    if key == "Descripcion del proyecto":
        proyecto_a_modificar.descripcion = val
    elif key == "Contadores":
        proyecto_a_modificar.contadores = val
    elif key == "Folio":
        proyecto_a_modificar.folio = val
    elif key == "Escritura":
        proyecto_a_modificar.escritura = val
    elif key == "Abogado":
        proyecto_a_modificar.abogado = val
    elif key == "Cliente":
        proyecto_a_modificar.cliente_principal = val
    elif key == "Faltantes":
        proyecto_a_modificar.faltantes = val
    

def obtener_faltantes(ruta_proyecto: str, CARPETA_LOGS_ACTO):
    cache_dir = os.path.join(ruta_proyecto, "_cache_bot", ARCHIVO_FALTANTES)
    data = leer_json(cache_dir)
    if not data:
        return None

    archivos_para_subir = {}

    proyecto_a_modificar = ProyectoMod()

    fecha_guardada = data.get("Fecha de registro")
    if not fecha_guardada:
        return None
    fecha_date = datetime.strptime(fecha_guardada, "%Y-%m-%d").date()
    hoy = date.today()
    diff = hoy-fecha_date
    dias_transcurridos = diff.days
    #YA NO SUBE NADA
    if dias_transcurridos > MINIMO_DE_DIAS: return None

    registrar_log(CARPETA_LOGS_ACTO, f"SE ENVIARÁ UN CORREO DENTRO DE {MINIMO_DE_DIAS-dias_transcurridos} DÍAS")

    proyecto_a_modificar.fecha = fecha_guardada

    for key, value in data.items():
        if key == "Fecha de registro":
            continue
        parsear(proyecto_a_modificar, key, value)
        
    #ACTUALIZAR ESCRITURA
    nombre_acto = os.path.basename(ruta_proyecto)
    #escritura = nombre_acto[:nombre_acto.find(".")]
    escritura = nombre_acto.split(".")[0]
    if escritura.lower() != "esc":
        proyecto_a_modificar.escritura = escritura

    faltantes = proyecto_a_modificar.faltantes or {}
    faltantes_nuevos = {}
    for key, docs in faltantes.items():
        docs_no_encontrados = []
        key_tuple = ast.literal_eval(key)
        tipo = key_tuple[0]
        nombre = key_tuple[1]
        carpetas = key_tuple[2].split("|")
        ruta = os.path.join(ruta_proyecto,*carpetas)
        for doc in docs:
            if tipo == "PF":
                ruta_encontrado = buscar_archivos_faltantes_pf(ruta, doc)
                if ruta_encontrado: 
                    if (nombre,tipo) in archivos_para_subir: archivos_para_subir[(nombre,tipo)].append([doc, ruta_encontrado])
                    else: archivos_para_subir[(nombre,tipo)] = [[doc, ruta_encontrado]]
                else: docs_no_encontrados.append(doc)
            elif tipo == "PM":
                ruta_encontrado = buscar_archivos_faltantes_pm(ruta, doc)
                if ruta_encontrado:
                    if (nombre,tipo) in archivos_para_subir: archivos_para_subir[(nombre,tipo)].append([doc, ruta_encontrado])
                    else: archivos_para_subir[(nombre,tipo)] = [[doc, ruta_encontrado]]
                else: docs_no_encontrados.append(doc)
            else: #Es Inmueble
                ruta_encontrado = buscar_archivos_faltantes_inmueble(ruta, doc)
                if ruta_encontrado:
                    if (nombre,"INM") in archivos_para_subir: archivos_para_subir[(nombre,"INM")].append([doc, ruta_encontrado])
                    else: archivos_para_subir[(nombre,"INM")] = [[doc, ruta_encontrado]]
                else: docs_no_encontrados.append(doc)

        if len(docs_no_encontrados)>0:
            faltantes_nuevos[key] = docs_no_encontrados

    if len(faltantes_nuevos) > 0: proyecto_a_modificar.faltantes_nuevos = faltantes_nuevos

    if archivos_para_subir:
        proyecto_a_modificar.archivos_para_subir = archivos_para_subir

    return proyecto_a_modificar

def guardar_json(data, carpeta: str, nombre_archivo: str):
    if not isinstance(data, dict):
        datos_proyecto = asdict(data)
    else: 
        datos_proyecto = data
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    ruta_completa = os.path.join(carpeta, nombre_archivo)
    with open(ruta_completa, "w", encoding="utf-8") as f:
        json.dump(datos_proyecto, f, indent=4, ensure_ascii=False)

def agregar_en_bitacora(data: dict, carpeta_abogado: str):
    with open(os.path.join(carpeta_abogado, "bitacora.json"), 'a', encoding='utf-8') as f:
        linea = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        f.write(linea + '\n')

def checar_fecha_valida(proyectoMod: ProyectoMod, CARPETA_LOGS_ACTO, nombre_carpeta: str, carpeta_abogado:str):
    fecha_guardada = proyectoMod.fecha
    fecha_date = datetime.strptime(fecha_guardada, "%Y-%m-%d").date()
    hoy = date.today()
    diff = hoy-fecha_date
    dias_transcurridos = diff.days
    if dias_transcurridos - MINIMO_DE_DIAS == 0:
        registrar_log(CARPETA_LOGS_ACTO, f"LIMITE DE {MINIMO_DE_DIAS} DÍAS TRANSCURRIDO")
        if len(proyectoMod.faltantes_nuevos)>0:
            bitacora_proyecto = {"Proyecto":nombre_carpeta}
            docs_por_cliente = {}
            for cliente, docs in proyectoMod.faltantes_nuevos.items():
                cliente_tupla = ast.literal_eval(cliente)
                docs_por_cliente[cliente_tupla[1]] = []
                for doc in docs:#Agregar todos los docs de ese cliente
                    docs_por_cliente[cliente_tupla[1]].append(doc)
            bitacora_proyecto["Faltantes"] = docs_por_cliente
            agregar_en_bitacora(bitacora_proyecto,carpeta_abogado)
            
def generar_excel(ruta_bitacora: str) -> str:
    # 1. Leer la bitácora (JSON Lines)
    datos_lista = []
    with open(os.path.join(ruta_bitacora, 'bitacora.json'), 'r', encoding='utf-8') as f:
        for linea in f:
            datos_lista.append(json.loads(linea))

    # 2. Aplanar los datos para que queden "chidos" en Excel
    filas_excel = []
    for acto in datos_lista:
        # Convertimos el dict de clientes a un string legible con saltos de línea
        # Ejemplo: "SERGIO: UIF, CURP | ARACELI: ACTA"
        resumen_clientes = ""
        for cliente, docs in acto["Faltantes"].items():
            resumen_clientes += f"• {cliente}: {', '.join(docs)}\n"
        
        filas_excel.append({
            "Proyecto": acto["Proyecto"],
            "Detalle de Faltantes": resumen_clientes.strip()
        })

    df = pd.DataFrame(filas_excel)

    # 3. Crear el Excel con formato "Chidote"
    ruta_excel = os.path.join(ruta_bitacora,'Resumen Proyectos.xlsx')
    writer = pd.ExcelWriter(ruta_excel, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Pendientes')

    workbook  = writer.book
    worksheet = writer.sheets['Pendientes']

    # --- FORMATOS ---
    header_format = workbook.add_format({
        'bold': True, 'text_wrap': True, 'valign': 'top',
        'fg_color': '#1F4E78', 'font_color': 'white', 'border': 1
    })

    cell_format = workbook.add_format({
        'text_wrap': True, 'valign': 'top', 'border': 1
    })

    # Aplicar formato a los encabezados
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Ajustar el ancho de las columnas y aplicar formato de celda
    worksheet.set_column('A:A', 30, cell_format) # Columna Proyecto
    worksheet.set_column('B:B', 60, cell_format) # Columna Clientes/Faltantes

    writer.close()
    return ruta_excel