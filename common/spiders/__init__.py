import json
import logging

from hashlib import sha256
from typing import Union, Optional, List, Dict, Any, Iterator
from bs4 import BeautifulSoup, Tag
from common.browser import Browser
from common.parser import ItemParser
from common.documents import SpiderTask, SpiderItem, data_digest_fn

from .paginated_scrollable_spider import PaginatedScrollableSpider


logger = logging.Logger(__name__)


class Spider:
    def __init__(self, browser: Browser, parser: ItemParser):
        self._browser = browser
        self._parser = parser

    @property
    def state(self):
        pass

    def will_open_url(self, browser: Browser, task: SpiderTask):
        pass

    def did_open_url(self, browser: Browser, task: SpiderTask):
        pass

    def will_start_parsing(self, browser: Browser, task: SpiderTask):
        pass

    def did_finish_parsing(self, browser: Browser, task: SpiderTask):
        pass


    def scrape(self, task: SpiderTask):
        for i, url in enumerate(task.urls):
            self._logger.info(f"goto url {url}")

            self.will_open_url(self._browser, task.model_copy(deep=True))
            self._browser.get(url)
            self.did_open_url(self._browser, task.model_copy(deep=True))

            self.will_start_parsing(self._browser)
            html = self._browser.page_source
            soup = BeautifulSoup(html, "lxml")
            for j, data in enumerate(self._parser.parse(soup)):
                digest = data_digest_fn(data, task.digest_v)
                item = SpiderItem(data=data,
                                  digest_v=task.digest_v,
                                  digest=digest,
                                  task_id=task.task_id)
                yield item
            self.did_finish_parsing(self._browser)

            self._browser.close_window()

    def stop(self):
        pass



__all__ = [
    'Spider',
    'PaginatedScrollableSpider',
]
