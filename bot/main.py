# bot/main.py

from bot.Proceso.procesar_abogados import proceso_por_abogado

import typer

app = typer.Typer(add_completion=False, no_args_is_help=False)


def _pipeline(headless: bool) -> None:
    """
    Pipeline principal del bot:
    solo delega todo a proceso_por_abogado.
    """
    #proceso_por_abogado(headless)
    
    import os
    from bot.core.acto_scanner import scan_acto_folder
    from bot.JSON.procesar_folder import Folder
    from bot.core.acto_detector import ActoResolver

    ruta = r"C:\Users\mdani\OneDrive\Desktop\Botbi\Carpeta_Notaria84\BOT SINGRAFOS BOTBI\\"
    #proyecto = "ESC.- Adjudicacion - Alfredo - INM 32"
    proyecto = "ESC.- Testamento - Daniel"
    #proyecto = "ESC.- Adjudicacion - Daniel - INM 1002"
    #proyecto = "ESC.- CANCELACION DE USUFRUCTO, COMPRAVENTA - EDUARDO REYES - RUBEN"
    #proyecto = "ESC.- CANCELACION DE USUFRUCTO, COMPRAVENTA - DANIEL JUAREZ- ALFREDO"
    acto = ruta + proyecto
    resolver = ActoResolver()
    actos_folder = Folder()
    left, middle, right = resolver._split_por_guiones(os.path.basename(acto))
    escritura, titulo = resolver._extraer_escritura_y_titulo(left)
    descripcion = " – ".join(filter(None, [titulo, middle, right]))
    
    # 3) Escanear y guardar JSON
    extraction = scan_acto_folder(acto, acto_nombre=os.path.basename(acto))
    json_path = actos_folder._ensure_cache_and_write_json(acto, extraction)

    print("Actos relacionados: ",getattr(extraction, "actos_relacionados"))

    pf_list, pm_list = actos_folder._extract_partes_pf_pm(extraction)

    acto_nombre = getattr(extraction, "acto_nombre", os.path.basename(acto))
    cliente_principal = getattr(extraction, "cliente_principal")
    inm_list = getattr(extraction, "inmuebles")

    #Guarda el json
    json_path = actos_folder._ensure_cache_and_write_json(acto, extraction)

    print("Personas fisicas")
    for pf in pf_list:
        #print(pf)
        print(f"\nNombre: {pf.get("nombre")}, Rol: {pf.get("rol")}, acto: {pf.get("acto_perteneciente")}")
        print("Conyugues")
        l = pf.get("esposa_o_esposo")
        if l:
            print(f"Nombre: {l.get("nombre")}, Rol: {l.get("rol")}, acto: {l.get("acto_perteneciente")}")
    print("\n\nPersonas morales")
    for pm in pm_list:
        print(f"\nNombre: {pm.get("nombre")}, Rol: {pm.get("rol")}, acto: {pm.get("acto_perteneciente")}")
        print("Representantes")
        rs = pm.get("representantes")
        for r in rs:
            print(f"~Nombre: {r.get("nombre")}, Rol: {r.get("ror")}, acto: {r.get("acto_perteneciente")}")

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
