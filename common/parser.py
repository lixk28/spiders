import lxml
import logging

from typing import Optional, Dict, Any, Iterator
from common.documents import SpiderItem
from bs4 import BeautifulSoup, Tag



class ItemParser:
    def parse(self, soup: BeautifulSoup) -> Iterator[Dict[str, Any]]:
        yield {}

        # items = soup.select(self.item_selector)
        # results = []
        # for i, item in enumerate(items):
        #     data = self.parse_item(item)
        #     result = SpiderItem(data=data)
        #     results.append(result)

__all__ = [
    'ItemParser',
]
