import abc

from typing import Callable, List, Dict
from common.browser import Browser
from common.handlers import ScrollingHandler, PaginationHandler
from . import Spider

# 分页、可滚动网页爬虫, 适用于大多数场景
class PaginatedScrollableSpider(Spider):
    def __init__(self,
                 browser: Browser,
                 scrolling_handler: ScrollingHandler,
                 pagination_handler: PaginationHandler):
        super(PaginatedScrollableSpider, self).__init__(self, browser)
        self.scrolling_handler = ScrollingHandler(browser)
        self.pagination_handler = PaginationHandler(browser)

    def run(self):
        self.browser.start()

    def stop(self):
        pass



__all__ = [
    'PaginatedScrollableSpider',
]
