from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

def make_driver(headless: bool = False, page_load_timeout: int = 60, wait_timeout: int = 20):
    opts = Options()
    if headless:
        # Headless moderno de Chrome
        opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    # Selenium Manager resuelve el driver automáticamente
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(page_load_timeout)
    wait = WebDriverWait(driver, wait_timeout)
    return driver, wait