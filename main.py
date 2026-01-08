from Bot.procesos.procesar_abogados import proceso_por_abogado
from Bot.escaneos.extraccion import ExtraccionCarpeta
from Bot.helpers.carpetas import obtener_clientes_totales
from Bot.helpers.json import guardar_json

import typer, os

app = typer.Typer(add_completion=False, no_args_is_help=False)

def _pipeline(headless: bool) -> None:
    """
        Pipeline principal del bot:
        solo delega todo a proceso_por_abogado.
    """
    
    proceso_por_abogado(headless)
    

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
