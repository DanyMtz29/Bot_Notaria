import os
from dotenv import load_dotenv
from loguru import logger
from .browser import make_driver
from ..pages.login_page import LoginPage

def login_smoke(headless: bool = False, screenshot_path: str = "bot/logs/login_ok.png"):
    load_dotenv(dotenv_path="bot/config/.env")

    url = os.getenv("PORTAL_URL", "").strip()
    user = os.getenv("PORTAL_USER", "").strip()
    pwd = os.getenv("PORTAL_PASS", "").strip()

    if not url or not user or not pwd:
        raise RuntimeError("Faltan PORTAL_URL, PORTAL_USER o PORTAL_PASS en bot/config/.env")

    driver, wait = make_driver(headless=headless)
    logger.info(f"Abriendo portal: {url}")

    try:
        page = LoginPage(driver, wait)
        page.login(url, user, pwd)

        # Si llegó aquí, muy probablemente entró; guardamos evidencia
        driver.save_screenshot(screenshot_path)
        logger.success(f"Login OK. Screenshot -> {screenshot_path}")
    finally:
        driver.quit()