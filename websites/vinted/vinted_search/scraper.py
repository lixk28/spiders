import os
import sys
import json
import random
import logging
from typing import Optional, List, Tuple
from time import sleep
from datetime import datetime
from dataclasses import dataclass, asdict, field

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


from models import (
    VintedSearchItem,
    VintedSearchPage,
)


__all__ = [
    'VintedSearchScrapeTask',
    'VintedSearchScrapeResult',
    'VintedSearchScraper',
]


@dataclass
class VintedSearchScrapeTask:
    id: str
    search_text: str
    max_num_items: int
    max_num_pages: int
    scrape_item_page: bool

    @property
    def url(self) -> str:
        return f"https://www.vinted.com/catalog?search_text={self.search_text}"


@dataclass
class VintedSearchScrapeResult:
    task: VintedSearchScrapeTask = field(default_factory=VintedSearchScrapeTask)
    commit_ts: str = field(default="")
    launch_ts: str = field(default="")
    finish_ts: str = field(default="")
    pages: List[VintedSearchPage] = field(default_factory=list)

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



class VintedSearchScraper:
    def __init__(
        self,
        browser: str = 'firefox',
        verbose: bool = True,
        headless: bool = False,
        tasks: List[VintedSearchScrapeTask] = [],
    ) -> None:
        assert browser in ['firefox', 'chrome']
        if browser == 'chrome':
            raise RuntimeError("chrome is for losers, please use firefox")

        os.makedirs('logs', exist_ok=True)
        self.logger = logging.getLogger(name='VintedSearchScraper')
        self.logger.setLevel(logging.INFO)
        self.log_formatter = logging.Formatter(fmt="[%(levelname)s] %(asctime)s | %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

        if verbose:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(self.log_formatter)
            self.logger.addHandler(handler)

        self.tasks = tasks
        for task in self.tasks:
            # TODO: gen task uuid by {keyword+commit_ts}?
            assert task.id is not None and len(task.id) > 0

        ts = self._timestamp()
        self.result_map = dict(zip(
            [task.id for task in tasks],
            [VintedSearchScrapeResult(
                task=task,
                commit_ts=ts,
                launch_ts=ts,
                finish_ts=ts,
                pages=[]
            )]
        ))

        if headless:
            os.environ['MOZ_HEADLESS'] = '1'
        self.webdriver = webdriver.Firefox()

    # execute task sequentially
    def run(self):
        for task_idx, task in enumerate(self.tasks):
            handler = logging.FileHandler(filename=f'logs/{task.id}.log', mode='a')
            handler.setFormatter(self.log_formatter)
            self.logger.addHandler(handler)
            self._execute_task(task)
            self.logger.removeHandler(handler)

    def _execute_task(self, task: VintedSearchScrapeTask):
        self.result_map[task.id].launch_ts = self._timestamp()

        num_pages_scraped = 0
        num_items_scraped = 0

        self.webdriver.get(task.url)
        self.logger.info(msg=f"goto web page {task.url}")

        while True:
            self._wait_content()
            self._close_domain_popup()
            self._close_cookie_popup()

            items = self._do_scrape_items(scrape_item_page=task.scrape_item_page)
            self.logger.info(msg=f"scrape new items: {[item.url for item in items]}")

            self.result_map[task.id].pages.append(VintedSearchPage(
                page_idx=num_pages_scraped + 1,
                items=items
            ))

            self._save(result=self.result_map[task.id])

            # NOTE: pretend to not being a robot 🤖
            self._pretend_to_scroll(
                times=random.randint(5, 8),
                interval=(2, 4),
                scroll=random.randint(800, 1200)
            )

            num_pages_scraped += 1
            num_items_scraped += self.result_map[task.id].pages[-1].num_items

            if num_pages_scraped >= task.max_num_pages or num_items_scraped >= task.max_num_items:
                break

            self._goto_next_page()

        self._sleep(2, 4)
        self.webdriver.quit()
        self.logger.info(msg=f"task {task.id} finished with {self.result_map[task.id].num_pages} pages and {self.result_map[task.id].num_items} items")
        self.logger.info(msg=f"{self.webdriver} exited gracefully")


    def _do_scrape_items(self, scrape_item_page: bool = False) -> List[VintedSearchItem]:
        self._sleep(3, 5)
        items: List[VintedSearchItem] = []

        feed_item_divs = self.webdriver.find_elements(By.CSS_SELECTOR, "div[class^=feed-grid__item-content]")

        for feed_item_div in feed_item_divs:
            # is item in closet
            is_closet = "feed-grid__item--full-row" in feed_item_div.get_attribute('class')
            item_divs = feed_item_div.find_elements(By.CSS_SELECTOR, "div[class=new-item-box__container]")

            for item_div in item_divs:
                item = VintedSearchItem()
                item.id = item_div.get_attribute('data-testid').split('-')[-1]

                # NOTE: Some item has more than one thumbnails in a collage style, there might be several
                item_img_divs = item_div.find_elements(By.CSS_SELECTOR, "div[class^=new-item-box__image]")
                for item_img_div in item_img_divs:
                    try:
                        item_img = item_img_div.find_element(By.CSS_SELECTOR, "img[class=web_ui__Image__content]")
                        item.img_urls.append(item_img.get_attribute('src'))
                    except Exception as e:
                        pass

                # disgusting, ew...
                item_a = item_div.find_element(By.CSS_SELECTOR, "a[class^=new-item-box__overlay]")
                item.url = item_a.get_attribute('href').split('?')[0]
                item_info = item_a.get_attribute('title')
                split_idx = item_info.find('price')
                last_comma_idx = item_info[:split_idx].rfind(',')
                item.description = item_info[:split_idx][:last_comma_idx]
                price_brand_size = {}
                for kv in item_info[split_idx:].split(','):
                    k, v = kv.split(':')
                    k = k.strip()
                    v = v.strip()
                    price_brand_size[k] = v
                    if k == 'price':
                        item.price = v
                    elif k == 'brand':
                        item.brand = v
                    elif k == 'size':
                        item.size = v

                # I don't know why the fuck vinted has different data-testid for ordinary items and closet items
                item_title_p = item_div.find_element(By.CSS_SELECTOR, f"p[data-testid$='{item.id}--description-title']")
                item_subtitle_p = item_div.find_element(By.CSS_SELECTOR, f"p[data-testid$='{item.id}--description-subtitle']")
                item_price_p = item_div.find_element(By.CSS_SELECTOR, f"p[data-testid$='{item.id}--price-text']")

                if item_title_p is not None:
                    item.title = item_title_p.text
                if item_subtitle_p is not None:
                    item.subtitle = item_subtitle_p.text
                if item_price_p:
                    item.price = item_price_p.text

                # TODO: item.owner

                items.append(item)

        return items

    def _pretend_to_scroll(self, times: int, interval: Tuple[float, float], scroll: int):
        low = interval[0]
        high = interval[1]
        for _ in range(times):
            self._sleep(low, high)
            self.webdriver.execute_script(
                f"window.scrollTo({{ top: window.scrollY + {scroll}, left: 0, behavior: 'smooth' }});"
            )

    def _goto_next_page(self):
        self._sleep(1, 3)
        next_page_a = self.webdriver.find_element(
            By.CSS_SELECTOR,
            "a[data-testid=catalog-pagination--next-page]"
        )
        next_page_a.click()

    def _timestamp(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _sleep(self, t1: float, t2: float):
        sleep(random.uniform(t1, t2))

    def _wait_content(self):
        try:
            WebDriverWait(driver=self.webdriver, timeout=5).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "section[class=site-content]"
                ))
            )
        except:
            self.webdriver.quit()

    def _close_domain_popup(self):
        try:
            domain_close_btn = self.webdriver.find_element(
                By.CSS_SELECTOR,
                "button[data-testid=domain-select-modal-close-button]"
            )
            if domain_close_btn is not None:
                self._sleep(1, 3)
                domain_close_btn.click()
        except:
            pass

    def _close_cookie_popup(self):
        try:
            reject_cookie_btn = self.webdriver.find_element(
                By.CSS_SELECTOR,
                "button[id=onetrust-reject-all-handler]"
            )
            if reject_cookie_btn is not None:
                self._sleep(1, 3)
                reject_cookie_btn.click()
        except:
            pass

    def _save(self, result: VintedSearchScrapeResult):
        os.makedirs('results', exist_ok=True)
        result.finish_ts = self._timestamp()
        with open(f'results/{result.task.id}.json', 'w') as file:
            file.write(json.dumps(
                asdict(result)
            , ensure_ascii=False, indent=4))


if __name__ == "__main__":
    task = VintedSearchScrapeTask(
        id='123456789',
        search_text='earring',
        max_num_items=1000,
        max_num_pages=3,
        scrape_item_page=False,
    )

    scraper = VintedSearchScraper(
        tasks=[task],
        browser='firefox',
        verbose=True,
        headless=False,
    )

    scraper.run()
