from Bot.procesos.procesar_abogados import proceso_por_abogado
from Bot.escaneos.extraccion import ExtraccionCarpeta
from Bot.helpers.carpetas import obtener_clientes_totales
from Bot.helpers.json import guardar_json

import typer, os

app = typer.Typer(add_completion=False, no_args_is_help=False)

def prueba_carpeta(nombre_proyecto):

    try:
        ruta_carpeta = r"C:\Users\mdani\OneDrive\Desktop\Botbi\Carpeta_Notaria84\BOT SINGRAFOS BOTBI"
        ruta = os.path.join(ruta_carpeta, nombre_proyecto)
        ex = ExtraccionCarpeta(ruta)
        proyecto = ex.extraccion_de_datos()
        proyecto.abogado = os.path.basename(ruta_carpeta)
        clientes = obtener_clientes_totales(proyecto)
        guardar_json(proyecto, os.path.join(proyecto.ruta, "_cache_bot"), "Proyecto Analizado.json")
        for i in range(0, len(clientes)):
            print(f"{i+1}. Cliente")
            print(clientes[i])
            print("\n")
        print("\n")
    except Exception as e: 
        print(f"Ocurrio un error: {e}")
    


def _pipeline(headless: bool) -> None:
    """
        Pipeline principal del bot:
        solo delega todo a proceso_por_abogado.
    """
    
    proceso_por_abogado(headless)
    #prueba_carpeta("ESC.- Aclaracion - Daniel - Prueba Aclaracion")
    #prueba_carpeta("ESC.- Adjudicacion - Alfredo - INM 32")
    #prueba_carpeta("ESC.- Adjudicacion - Daniel - INM 1002")
    #prueba_carpeta("ESC.- CANCELACION DE USUFRUCTO, COMPRAVENTA - DANIEL JUAREZ- ALFREDO")
    #prueba_carpeta("ESC.- Compraventa - Daniel Juarez - 2PMs")
    #prueba_carpeta("ESC.- Compraventa - Daniel Juarez - PMs")
    #prueba_carpeta("ESC.- Testamento - Daniel")
    #prueba_carpeta(os.path.join("AFP (Actas Fuera de Protocolo)", "AFP .-Carta permiso - Sergio"))
    #prueba_carpeta(os.path.join("AFP (Actas Fuera de Protocolo)", "AFP.- EXTRAVIO DE DOCUMENTACION - DIANA GABRIELA"))
    #prueba_carpeta(os.path.join("AFP (Actas Fuera de Protocolo)", "AFP.- RATIFICACION FIRMAS - SERGIO ARMANDO"))
    #prueba_carpeta(os.path.join("AFP (Actas Fuera de Protocolo)", "AFP.- TESTIMONIAL VEHICULAR - SERGIO ARMANDO - Vehiculo"))
    

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
