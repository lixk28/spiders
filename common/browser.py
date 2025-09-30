import os
import json
import time
import logging
import random
import threading
import traceback

from enum import StrEnum
from typing import Optional, Union, Callable, List, Dict

from PIL import Image
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from common.decorators import retrying


class ElementState(StrEnum):
    Present = 'present'
    Visible = 'visible'
    Clickable = 'clickable'
    Selected = 'selected'
    Invisible = 'inivisible'


class ClickType(StrEnum):
    LeftClick = 'left_click'
    RightClick = 'right_click'
    DoubleClick = 'double_click'


class Browser:
    def __init__(self,
                 headless: bool = False,
                 viewport_width: int = 1920,
                 viewport_height: int = 1080,
                 user_agent: Optional[str] = None,
                 proxy: Optional[str] = None,
                 global_waits: float = 0.5):
        self.headless = headless

        options = Options()
        options.headless = headless

        service = Service()

        self.driver = webdriver.Firefox(options=options, service=service)
        # self.driver = webdriver.Chrome(keep_alive=True)

        self.logger = logging.getLogger(name='Browser')

        # TODO: driver 监听线程
        self.monitor = threading.Thread()

        self._initialized = False
        self._running = False


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    def launch(self):
        if self._initialized or self._running:
            return
        self._initialized = True
        self.logger.info("Browser started")


    def quit(self):
        self.driver.quit()
        self.driver = None
        self._initialized = False
        self._running = False
        self.logger.info("Browser quit")


    def get(self, url: str):
        self.driver.get(url)

    def forward(self) -> None:
        self.driver.forward()

    def back(self) -> None:
        self.driver.back()

    def refresh(self) -> None:
        self.driver.refresh()

    def close_window(self) -> None:
        self.driver.close()

    def wait_for(self, css_selector: str, to_be: ElementState, poll_every: float = 1, timeout: float = 16):
        if to_be == 'present':
            expected_condition = EC.presence_of_element_located
        elif to_be == 'visible':
            expected_condition = EC.visibility_of_element_located
        elif to_be == 'clickable':
            expected_condition = EC.element_to_be_clickable
        elif to_be == 'selected':
            expected_condition = EC.element_to_be_selected
        elif to_be == 'invisible':
            expected_condition = EC.invisibility_of_element_located
        else:
            raise ValueError(f"Invalid expected state for element: {to_be}")

        predicate = expected_condition((By.CSS_SELECTOR, css_selector))
        wait = WebDriverWait(self.driver, timeout=timeout, poll_frequency=poll_every)
        element = wait.until(predicate)
        return element

    # def wait_for_all(self, css_selector: str, to_be: ElementState, poll_every: float = 1, timeout: float = 16):
    #     def _predicate():
    #         elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
    #         # for ele


    @retrying.retry
    def query(self, css_selector: str, waiting: bool = True, **kwargs):
        if waiting:
            poll_every = float(kwargs.pop('poll_every', 1))
            timeout = float(kwargs.pop('timeout', 5))
            wait = WebDriverWait(self.driver, timeout=timeout, poll_frequency=poll_every)
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        else:
            return self.driver.find_element(By.CSS_SELECTOR, css_selector)

    @retrying.retry
    def query_all(self, css_selector: str, waiting: bool = True, **kwargs):
        if waiting:
            poll_every = float(kwargs.pop('poll_every', 1))
            timeout = float(kwargs.pop('poll_every', 5))
            wait = WebDriverWait(self.driver, timeout=timeout, poll_frequency=poll_every)
            return wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
        else:
            return self.driver.find_elements(By.CSS_SELECTOR, css_selector)


    def click_on_element(self, element: WebElement, click_type: ClickType):
        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        if click_type == ClickType.LeftClick:
            actions.click()
        elif click_type == ClickType.RightClick:
            actions.context_click()
        elif click_type == ClickType.DoubleClick:
            actions.double_click()
        actions.perform()


    def click_on(self, css_selector: str, click_type: ClickType = ClickType.LeftClick):
        clickable = self.wait_for(css_selector, to_be=ElementState.Clickable)
        return self.click_on_element(clickable, click_type=click_type)

    def left_click_on(self, css_selector: str):
        return self.click_on(css_selector, ClickType.LeftClick)

    def right_click_on(self, css_selector: str):
        return self.click_on(css_selector, ClickType.RightClick)

    def double_click_on(self, css_selector: str):
        return self.click_on(css_selector, ClickType.DoubleClick)

    def hover_over(self, css_selector: str):
        hoverable = self.wait_for(css_selector, to_be=ElementState.Visible)
        actions = ActionChains(self.driver)
        actions.move_to_element(hoverable)
        actions.perform()

        # element = self.query(css_selector)
        # if element is None:
        #     return False

        # if not self.query(css_selector, to_be=ElementState.Visible):
        #     return False

        # try:
        #     actions = ActionChains(self.driver)
        #     actions.move_to_element(element)
        #     actions.perform()
        #     return True
        # except Exception as e:
        #     self.logger.error(traceback.format_exc())
        #     self.logger.error(f"Error hovering over element {element}: {e}")
        #     return False

    def scroll_to(self, x: Union[float, str], y: Union[float, str]):
        script = f"window.scrollTo({{ top: {x}, left: {y}, behavior: 'smooth' }})"
        self.driver.execute_script(script)
        # try:
        #     script = f"window.scrollTo({{ top: {x}, left: {y}, behavior: 'smooth' }})"
        #     self.driver.execute_script(script)
        #     return True
        # except Exception as e:
        #     self.logger.error(traceback.format_exc())
        #     self.logger.error(f"Error scrolling to position x={x}, y={y}: {e}")
        #     return False
        # finally:
        #     self.driver.quit()
        #     return False


    def scroll_by(self, delta_x: Union[float, str], delta_y: Union[float, str]):
        script = f"window.scrollBy({{ top: {delta_x}, left: {delta_y}, behavior: 'smooth' }})"
        self.driver.execute_script(script)
        # try:
        #     script = f"window.scrollBy({{ top: {delta_x}, left: {delta_y}, behavior: 'smooth' }})"
        #     self.driver.execute_script(script)
        #     return True
        # except Exception as e:
        #     self.logger.error(traceback.format_exc())
        #     self.logger.error(f"Error scrolling by delta_x={delta_x}, delta_y={delta_y}: {e}")
        #     return False
        # finally:
        #     self.driver.quit()
        #     return False


    def scroll_vertically(self, offset: Union[float, str]):
        return self.scroll_by(delta_x=0, delta_y=offset)


    def scroll_down(self, by: float):
        by = abs(float(by))
        return self.scroll_vertically(offset=by)


    def scroll_up(self, by: float):
        by = -abs(float(by))
        return self.scroll_vertically(offset=by)


    def scroll_to_bottom(self):
        return self.scroll_to(x='window.scrollX', y='document.body.scrollHeight')


    def scroll_to_top(self):
        return self.scroll_to(x='window.scrollX', y='0')


    def scroll_to_element(self, css_selector: str):
        element = self.query(css_selector)
        if element is None:
            return False

    @property
    def screenshot(self):
        pass

    @property
    def timeouts(self):
        return self.driver.timeouts

    @property
    def cookies(self) -> list[dict]:
        return self.driver.get_cookies()

    def get_cookie(self, name):
        return self.driver.get_cookie(name)

    def set_cookie(self, cookie: dict):
        return self.driver.add_cookie(cookie)

    def delete_cookie(self, name):
        return self.driver.delete_cookie(name)

    def delete_all_cookies(self):
        return self.driver.delete_all_cookies()

    @property
    def capabilities(self) -> dict:
        return self.driver.capabilities

    @property
    def network(self):
        return self.driver.network

    @property
    def title(self):
        return self.driver.title

    @property
    def current_url(self):
        return self.driver.current_url

    @property
    def page_source(self):
        return self.driver.page_source

    @property
    def page_size(self):
        pass

    @property
    def page_height(self):
        pass

    @property
    def page_width(self):
        pass

    @property
    def body_size(self):
        pass


    @property
    def body_height(self):
        pass

    @property
    def body_width(self):
        pass


    @property
    def window_size(self):
        pass

    @property
    def window_height(self):
        pass


    @property
    def window_width(self):
        pass
