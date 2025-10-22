import os
import typer
from loguru import logger
from bot.core.auth import login_smoke

app = typer.Typer(add_completion=False)

@app.command("login-test")
def login_test(
    headless: bool = typer.Option(False, help="Ejecuta el navegador en modo headless"),
    screenshot: str = typer.Option("bot/logs/login_ok.png", help="Ruta del screenshot de evidencia")
):
    os.makedirs(os.path.dirname(screenshot), exist_ok=True)
    try:
        login_smoke(headless=headless, screenshot_path=screenshot)
    except Exception as e:
        logger.exception(e)
        raise typer.Exit(code=1)

@app.command("hello")
def hello():
    print("CLI OK")

if __name__ == "__main__":
    app()