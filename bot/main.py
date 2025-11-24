# bot/main.py

from bot.Proceso.procesar_abogados import proceso_por_abogado

import typer
from bot.utils.Logger import setup_logger


# Configurar logger principal solo una vez aquí
setup_logger("Proceso principal")

app = typer.Typer(add_completion=False, no_args_is_help=False)


def _pipeline(headless: bool) -> None:
    """
    Pipeline principal del bot:
    solo delega todo a proceso_por_abogado.
    """
    #proceso_por_abogado(headless)
    
    # import os
    # from bot.core.acto_scanner import scan_acto_folder
    # from bot.JSON.procesar_folder import Folder
    # from bot.core.acto_detector import ActoResolver
    # from bot.core.faltantes import FaltantesService

    # ruta = r"C:\Users\mdani\OneDrive\Desktop\Botbi\Carpeta_Notaria84\BOT SINGRAFOS BOTBI\\"
    # proyecto = "ESC. Compraventa - Daniel"
    # acto = ruta + proyecto
    # resolver = ActoResolver()
    # actos_folder = Folder()
    # left, middle, right = resolver._split_por_guiones(os.path.basename(acto))
    # escritura, titulo = resolver._extraer_escritura_y_titulo(left)
    # descripcion = " – ".join(filter(None, [titulo, middle, right]))
    
    # # 3) Escanear y guardar JSON
    # extraction = scan_acto_folder(acto, acto_nombre=os.path.basename(acto))

    # pf_list, pm_list = actos_folder._extract_partes_pf_pm(extraction)

    # acto_nombre = getattr(extraction, "acto_nombre", os.path.basename(acto))
    # cliente_principal = getattr(extraction, "cliente_principal")
    # inm_list = getattr(extraction, "inmuebles")

    # #Guarda el json
    # json_path = actos_folder._ensure_cache_and_write_json(acto, extraction)

    # all_parties = actos_folder._flatten_all_parties(pf_list, pm_list)
    # partes = []
    # for cl in pf_list:
    #     partes.append(cl)
    # for cl in pm_list:
    #     partes.append(cl)

    # clientes = []
    # for parte in partes:
    #     if parte.get("tipo") == "PM":
    #         clientes.append(parte.get("representante", {}))
    #     else:
    #         if parte.get("esposa_o_esposo"):
    #             clientes.append(parte.get("esposa_o_esposo", {}))
    #     clientes.append(parte)

    import json

    ruta = r"C:\Users\mdani\OneDrive\Desktop\Botbi\Carpeta_Notaria84\BOT SINGRAFOS BOTBI\ESC. Compraventa - Daniel\_cache_bot\acto.json"
    ruta_abs = r"C:\Users\mdani\OneDrive\Desktop\Botbi\Carpeta_Notaria84\BOT SINGRAFOS BOTBI\ESC. Compraventa - Daniel"
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)

    # pf_list = data.get("data", []).get("partes_pf", [])
    # pm_list = data.get("data", []).get("partes_pm", [])

    from bot.JSON.procesar_folder import Folder
    from bot.core.acto_scanner import scan_acto_folder
    import os
    actos_folder = Folder()
    extraction = scan_acto_folder(ruta_abs, acto_nombre=os.path.basename(ruta_abs))
    pf_list, pm_list = actos_folder._extract_partes_pf_pm(extraction)

    partes = []
    for cl in pf_list:
        print(f"\n\nCliente: {cl.get("nombre","")}")
        print(cl)
        partes.append(cl)
    for cl in pm_list:
        print(f"\n\nCliente: {cl.get("nombre","")}")
        print(cl)
        partes.append(cl)

    clientes = []
    for parte in partes:
        if parte.get("tipo") == "PM":
            clientes.append(parte.get("representante", {}))
        else:
            if parte.get("esposa_o_esposo"):
                clientes.append(parte.get("esposa_o_esposo", {}))
        clientes.append(parte.get("persona", parte))

    print("\n\n")
    for cl in clientes:
        print(f"Tipo de dato: {type(cl)}")
        print(f"Nombre: {cl.get('nombre')}, RFC: {cl.get('rfc')}")


    print("ESTRACTION COMPLETADA")



# =========================
# CLI
# =========================
@app.callback(invoke_without_command=True)
def _default(
    ctx: typer.Context,
    headless: bool = typer.Option(
        False,
        help="Ejecuta navegador en modo headless",
    ),
):
    """
    Sin subcomando: ejecuta el pipeline por defecto.
    Con subcomando `run`: hace lo mismo.
    """
    if ctx.invoked_subcommand is None:
        _pipeline(headless=headless)


@app.command("run")
def run(
    headless: bool = typer.Option(
        False,
        help="Ejecuta navegador en modo headless",
    ),
):
    """Ejecuta el pipeline principal (alias)."""
    _pipeline(headless=headless)


if __name__ == "__main__":
    app()


"""
.venv\scripts\activate
python -m bot.main --no-headless
"""