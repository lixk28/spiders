import os
import sys
import json
import random
import logging
from typing import Optional, List, Tuple, Set
from time import sleep
from datetime import datetime
from dataclasses import dataclass, field, asdict

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from models import (
    MercariSearchItem,
)

__all__ = [
    'MercariSearchTask',
    'MercariSearchResult',
    'MercariSearchScraper',
]


@dataclass
class MercariSearchTask:
    id: str = field(default=None)
    keyword: str = field(default="")
    filters: List[str] = field(default_factory=list)
    max_num_items: int = field(default=1000)
    scrape_item_page: bool = False

    @property
    def search_text(self) -> str:
        search_text = self.keyword
        for filter in self.filters:
            search_text += f' -{filter}'
        return search_text

    @property
    def url(self) -> str:
        return f"https://www.mercari.com/search/?keyword={self.search_text}"


@dataclass
class MercariSearchResult:
    task: MercariSearchTask = field(default_factory=MercariSearchTask)
    commit_ts: str = field(default="")
    launch_ts: str = field(default="")
    finish_ts: str = field(default="")
    items: List[MercariSearchItem] = field(default_factory=list)


class MercariSearchScraper:
    def __init__(
        self,
        max_num_threads: int = 4,
        max_num_tasks: int = 16,
        browser: str = 'firefox',
        verbose: bool = True,
        headless: bool = False,
        tasks: List[MercariSearchTask] = []
    ) -> None:
        assert browser in ['firefox', 'chrome']
        if browser == 'chrome':
            raise RuntimeError("chrome is for losers, please use firefox")

        os.makedirs('logs', exist_ok=True)
        self.logger = logging.getLogger(name='MercariSearchScraper')
        self.logger.setLevel(logging.INFO)
        self.log_formatter = logging.Formatter(fmt="[%(levelname)s] %(asctime)s | %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

        if verbose:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(self.log_formatter)
            self.logger.addHandler(handler)

        # TODO: does nothing, no multithread support for now
        self.max_num_threads = max_num_threads
        self.max_num_tasks = max_num_tasks

        self.tasks = tasks
        for task in self.tasks:
            # TODO: gen task uuid by {keyword+commit_ts}?
            assert task.id is not None and len(task.id) > 0

        ts = self._timestamp()
        self.result_map = dict(zip(
            [task.id for task in tasks],
            [MercariSearchResult(
                task=task,
                commit_ts=ts,
                launch_ts=ts,
                finish_ts=ts,
                items=[]
            ) for task in tasks]
        ))

        if headless:
            os.environ['MOZ_HEADLESS'] = '1'
        self.webdriver = webdriver.Firefox()

    @property
    def num_tasks(self) -> int:
        return len(self.tasks)

    def commit_task(self, task: MercariSearchTask):
        # ts = self._timestamp()
        # task.id = f"{task.keyword}_{ts}"
        self.tasks.append(task)

    def run(self):
        for task_idx, task in enumerate(self.tasks):
            handler = logging.FileHandler(filename=f'logs/{task.id}.log', mode='a')
            handler.setFormatter(self.log_formatter)
            self.logger.addHandler(handler)
            self._execute_task(task)
            self.logger.removeHandler(handler)

    def _execute_task(self, task: MercariSearchTask):
        self.result_map[task.id].launch_ts = self._timestamp()
        item_set = set()

        self.webdriver.get(task.url)
        self.logger.info(msg=f"goto web page {task.url}")

        while True:
            self._wait_search_page_content()
            self._agree_privacy_settings()

            self._sleep(4, 6)

            item_divs = self.webdriver.find_elements(By.CSS_SELECTOR, "div[id][data-itemprice][data-itemstatus]")

            items = self._do_scrape_items(item_set, item_divs, task.scrape_item_page)
            self.logger.info(msg=f"scrape new items: {[item.url for item in items]}")

            item_set.update(items)
            self.result_map[task.id].items = list(item_set)
            self.save(result=self.result_map[task.id])
            self._sleep(2, 4)

            if len(item_set) >= task.max_num_items:
                break

            self._scroll(offset=[800, 1200])

        self.webdriver.quit()
        self.logger.info(msg=f"task {task.id} finished with {len(self.result_map[task.id].items)} items scraped")
        self.logger.info(msg=f"{self.webdriver} exited gracefully")

    def _wait_search_page_content(self):
        try:
            WebDriverWait(driver=self.webdriver, timeout=8).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div[data-testid=Search-Items]"
                ))
            )
        except:
            self.webdriver.quit()

    def _wait_item_page_content(self):
        try:
            WebDriverWait(driver=self.webdriver, timeout=8).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div[data-testid=ItemDetailColPhotos]"
                ))
            )
        except:
            self.webdriver.quit()

    def _agree_privacy_settings(self):
        try:
            btn = self.webdriver.find_element(
                By.CSS_SELECTOR,
                "button[id=truste-consent-button]"
            )
            if btn is not None:
                self._sleep(1, 3)
                btn.click()
        except:
            pass

    def _do_scrape_items(
        self,
        item_set: Set[MercariSearchItem],
        item_divs: List[WebElement],
        scrape_item_page: bool = False
    ) -> List[MercariSearchItem]:
        items: List[MercariSearchItem] = []

        for item_div in item_divs:
            item = MercariSearchItem()

            item.id = item_div.get_attribute('id')
            if item in item_set:
                continue

            item.status = item_div.get_attribute('data-itemstatus')

            item_a = item_div.find_element(By.CSS_SELECTOR, "a[data-testid=ProductThumbWrapper]")
            item.url = item_a.get_attribute('href').split('?')[0].removesuffix('/')

            item_metas = item_a.find_elements(By.CSS_SELECTOR, "meta")
            for item_meta in item_metas:
                prop = item_meta.get_attribute('itemprop')
                content = item_meta.get_attribute('content')
                if prop == 'category' and content is not None:
                    item.category = content
                elif prop == 'brand' and content is not None:
                    item.brand = content
                elif prop == 'itemCondition' and content is not None:
                    item.condition = content
                elif prop == 'description' and content is not None:
                    item.description = content
                elif prop == 'color' and content is not None:
                    item.color  = content

            try:
                item_decor_span = item_a.find_element(By.CSS_SELECTOR, "span[data-testid=ItemDecorationRectangle]")
                item.decoration = item_decor_span.text
            except:
                pass

            item_price_p = item_div.find_element(By.CSS_SELECTOR, "p[data-testid=ProductThumbItemPrice]")
            item.price = item_price_p.text

            if not scrape_item_page:
                item_img = item_div.find_element(By.CSS_SELECTOR, "div[class^=Product__CDNImageWrapper] > img")
                item.img_urls = [item_img.get_attribute('src').split('?')[0].replace('thumb/', '')]

            items.append(item)

        if scrape_item_page:
            for item in items:
                item.img_urls = self._do_scrape_item_page(item.url)
                self._wait_search_page_content()

        return items

    # NOTE: Only scrape images from item page for now
    def _do_scrape_item_page(self, item_url: str):
        self.webdriver.get(item_url)
        self.logger.info(msg=f"goto web page {item_url}")

        self._wait_item_page_content()
        item_imgs = self.webdriver.find_elements(
            By.CSS_SELECTOR,
            "div[class^=PhotoIndicators__ImageWrapper] > img"
        )
        item_img_urls = [img.get_attribute('src').split('?')[0] for img in item_imgs]
        self._sleep(2, 3)

        # FIXME: sometimes the search page jumps to bottom after going back
        self.webdriver.back()
        self.logger.info(msg=f"goback from {item_url}")

        return item_img_urls

    def _scroll(self, offset: Tuple[float, float]):
        self.webdriver.execute_script(
            f"window.scrollTo({{ top: window.scrollY + {random.uniform(offset[0], offset[1])}, left: 0, behavior: 'smooth' }});"
        )

    def _timestamp(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _sleep(self, t1: float, t2: float):
        sleep(random.uniform(t1, t2))

    def save(self, result: MercariSearchResult):
        result.finish_ts = self._timestamp()
        os.makedirs('results', exist_ok=True)
        with open(f'results/{result.task.id}.json', 'w') as file:
            file.write(json.dumps(
                asdict(result)
            , ensure_ascii=False, indent=4))


if __name__ == "__main__":
    task = MercariSearchTask(
        id='123456789',
        keyword='T-Shirt',
        filters=['Dress', 'Long'],
        max_num_items=1000,
        scrape_item_page=False
    )

    scraper = MercariSearchScraper(
        tasks=[task],
        browser='firefox',
        verbose=True,
        headless=False
    )

    scraper.run()
