import logging
import traceback

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger("Browser")

class HTMLElement(WebElement):
    @property
    def classes(self):
        return self.get_attribute("class").split(" ")


    def find_element(self, css_selector: str):
        try:
            element = super().find_element(By.CSS_SELECTOR, css_selector)
            return element
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Error finding child elements of {self} with selector {css_selector}: {e}")
            return None

    def find_elements(self, css_selector: str):
        try:
            elements = super().find_elements(By.CSS_SELECTOR, css_selector)
            return elements
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Error finding child elements of {self} with selector {css_selector}: {e}")
            return []


class HTMLAnchorElement(HTMLElement):
    @property
    def href(self):
        return self.get_attribute('href')


class HTMLImgElement(HTMLElement):
    @property
    def src(self):
        return self.get_attribute("src")

    @property
    def alt(self):
        return self.get_attribute("alt")
