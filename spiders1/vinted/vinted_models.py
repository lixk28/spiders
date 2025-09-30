import uuid
from typing import List
from pydantic import BaseModel
from datetime import datetime


class VintedSearchItem(BaseModel):
    id: str = ''
    url: str = ''
    owner: str = ''
    title: str = ''
    subtitle: str = ''
    description: str = ''
    brand: str = ''
    price: str = ''
    size: str = ''
    img_urls: List[str] = []

    @property
    def num_imgs(self) -> int:
        return len(self.img_urls)


class VintedSearchPage(BaseModel):
    page_idx: int = -1
    items: List[VintedSearchItem] = []

    @property
    def num_items(self) -> int:
        return len(self.items)


class VintedSearchScrapeTask(BaseModel):
    id: str = uuid.uuid5()
    search_text: str = ''
    max_num_items: int = 0
    max_num_pages: int = 0
    should_scrape_item_page: bool = False

    @property
    def url(self) -> str:
        return f"https://www.vinted.com/catalog?search_text={self.search_text}"


class VintedSearchScrapeResult(BaseModel):
    task: VintedSearchScrapeTask = VintedSearchScrapeTask()
    commit_ts: datetime
    launch_ts: datetime
    finish_ts: datetime
    pages: List[VintedSearchPage] = []

    @property
    def items(self) -> List[VintedSearchItem]:
        lll = []
        for page in self.pages:
            lll.extend(page.items)
        return lll

    @property
    def num_pages(self) -> int:
        return len(self.pages)

    @property
    def num_items(self) -> int:
        return sum([page.num_items for page in self.pages])

    @property
    def num_imgs(self) -> int:
        return sum([item.num_imgs for item in self.items])



__all__ = [
    'VintedSearchItem',
    'VintedSearchPage',
    'VintedSearchScrapeTask',
    'VintedSearchScrapeResult',
]
