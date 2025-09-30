from abc import ABC, abstractmethod
from typing import Optional, Tuple
from common.browser import Browser
from selenium.webdriver.common.by import By

class PaginationHandler(ABC):
    def __init__(self,
                 browser: Browser,
                 page: Optional[int],
                 prev_page_selector: Optional[str] = None,
                 next_page_selector: Optional[str] = None):
        self.browser = browser
        self._page = page if page is not None else 1
        self._prev_page_selector = prev_page_selector
        self._next_page_selector = next_page_selector

    @property
    def page(self) -> int:
        return self._page

    @page.setter
    def page(self, page: int):
        self._page = page

    @abstractmethod
    def goto_next_page(self):
        pass

    @abstractmethod
    def goto_prev_page(self):
        pass

    # immediately called after goto_next_page()
    def on_next_page(self):
        self._page += 1

    # immediately called after goto_prev_page()
    def on_prev_page(self):
        self._page -= 1



class DefaultPaginationHandler(PaginationHandler):
    def __init__(self,
                 browser: Browser,
                 page: Optional[int],
                 prev_page_selector: Optional[str] = None,
                 next_page_selector: Optional[str] = None):
        super().__init__(browser, page, prev_page_selector, next_page_selector)

    def goto_prev_page(self):
        if self._prev_page_selector is None:
            return False
        success = self.browser.left_click_on(self._prev_page_selector)
        if success:
            self.on_prev_page()
        return success

    def goto_next_page(self):
        if self._next_page_selector is None:
            return False
        success = self.browser.left_click_on(self._next_page_selector)
        if success:
            self.on_next_page()
        return success


__all__ = [
    'PaginationHandler',
    'DefaultPaginationHandler',
]
