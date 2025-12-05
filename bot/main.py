# bot/main.py

from bot.Proceso.procesar_abogados import proceso_por_abogado

import typer

app = typer.Typer(add_completion=False, no_args_is_help=False)


def _pipeline(headless: bool) -> None:
    """
    Pipeline principal del bot:
    solo delega todo a proceso_por_abogado.
    """
    proceso_por_abogado(headless)
    
    # import os
    # from bot.core.acto_scanner import scan_acto_folder
    # from bot.JSON.procesar_folder import Folder
    # from bot.core.acto_detector import ActoResolver
    # from bot.core.faltantes import FaltantesService

    # ruta = r"C:\Users\mdani\OneDrive\Desktop\Botbi\Carpeta_Notaria84\BOT SINGRAFOS BOTBI\\"
    # #proyecto = "ESC. Aclaracion - Daniel - Prueba Aclaracion"
    # #proyecto = "ESC.- Adjudicacion - Daniel - INM 1002"
    # proyecto = "ESC.- CANCELACION DE USUFRUCTO, COMPRAVENTA - EDUARDO REYES - RUBEN"
    # #proyecto = "ESC.- CANCELACION DE USUFRUCTO, COMPRAVENTA - EDUARDO REYES - RUBEN"
    # acto = ruta + proyecto
    # resolver = ActoResolver()
    # actos_folder = Folder()
    # left, middle, right = resolver._split_por_guiones(os.path.basename(acto))
    # escritura, titulo = resolver._extraer_escritura_y_titulo(left)
    # descripcion = " – ".join(filter(None, [titulo, middle, right]))
    
    # # 3) Escanear y guardar JSON
    # extraction = scan_acto_folder(acto, acto_nombre=os.path.basename(acto))
    # json_path = actos_folder._ensure_cache_and_write_json(acto, extraction)

    # print(getattr(extraction, "actos_relacionados"))

    # pf_list, pm_list = actos_folder._extract_partes_pf_pm(extraction)

    # acto_nombre = getattr(extraction, "acto_nombre", os.path.basename(acto))
    # cliente_principal = getattr(extraction, "cliente_principal")
    # inm_list = getattr(extraction, "inmuebles")

    # #Guarda el json
    # json_path = actos_folder._ensure_cache_and_write_json(acto, extraction)

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