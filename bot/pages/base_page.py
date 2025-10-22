from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    def __init__(self, driver: WebDriver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    def open(self, url: str):
        self.driver.get(url)

    def find_first(self, locators):
        """
        Intenta varios localizadores y devuelve el primero que aparezca.
        locators: lista de tuplas (By, selector)
        """
        last_exc = None
        for by, sel in locators:
            try:
                return self.wait.until(EC.presence_of_element_located((by, sel)))
            except Exception as e:
                last_exc = e
        raise last_exc or Exception("Element not found with any locator.")

    def click_when_clickable(self, locator):
        return self.wait.until(EC.element_to_be_clickable(locator))