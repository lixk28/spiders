import os
import sys
import traceback
cwd = os.getcwd()
sys.path.append(cwd)

import json
import random
import logging
from typing import Optional, List, Tuple
from time import sleep
from datetime import datetime

from selenium.webdriver.common.by import By
from common.browser import Browser, ElementState
from common.documents import SpiderTask, SpiderItem
from common.db_client import DBClient, DatabaseType


class VintedSearchSpider:
    def __init__(self) -> None:
        self.browser = Browser()
        self.browser.launch()
        self.logger = logging.getLogger(__name__)
        self.tasks = []
        self.db_client = DBClient(db_type=DatabaseType.TEST)

    def submit(self, task: SpiderTask):
        self.tasks.append(task)

    def run(self):
        for i, task in enumerate(self.tasks):
            try:
                self._run_task(task)
            except Exception as e:
                self.logger.error(traceback.format_exc())
                self.logger.error(f"Task {task.task_id} failed: {e}")
            finally:
                self.browser.quit()
                break

    def _run_task(self, task: SpiderTask):
        self.browser.get(task.url)
        print(f"goto url {task.url}")

        self._close_domain_popup()
        self._close_cookie_popup()
        self._wait_content()

        n_scraped_pages = 0
        n_scraped_items = 0

        while True:
            items = self._do_scrape_items(task)

            self._scroll_down_randomly()
            self._goto_next_page()

            n_scraped_pages += 1
            n_scraped_items += len(items)

            if n_scraped_pages >= task.max_pages or n_scraped_items >= task.max_items:
                print("reach max pages or items, finish scraping")
                break


    def _save(self, task: SpiderTask, items: List[SpiderItem]):
        docs = [t.model_dump() for t in items]
        result = self.db_client.insert(collection_name='vinted-search', documents=docs)
        if not result.acknowledged:
            print("insert failed")
            return

    def _do_scrape_items(self, task: SpiderTask):
        items: List[SpiderItem] = []

        feed_item_divs = self.browser.query_all("div[class^=feed-grid__item-content]")
        for feed_item_div in feed_item_divs:
            # is item in closet
            is_closet = "feed-grid__item--full-row" in feed_item_div.get_attribute('class')
            item_divs = feed_item_div.find_elements(By.CSS_SELECTOR, "div[class=new-item-box__container]")

            for item_div in item_divs:
                data = {
                    'id': '',
                    'url': '',
                    'owner': '',
                    'title': '',
                    'subtitle': '',
                    'description': '',
                    'brand': '',
                    'price': '',
                    'size': '',
                    'img_urls': []
                }

                data['id'] = item_div.get_attribute('data-testid').split('-')[-1]

                # NOTE: Some item has more than one thumbnails in a collage style, there might be several
                item_img_divs = item_div.find_elements(By.CSS_SELECTOR, "div[class^=new-item-box__image]")
                for item_img_div in item_img_divs:
                    try:
                        item_img = item_img_div.find_element(By.CSS_SELECTOR, "img[class=web_ui__Image__content]")
                        data['img_urls'].append(item_img.get_attribute('src'))
                    except Exception as e:
                        pass

                # # disgusting, ew...
                # item_a = item_div.find_element(By.CSS_SELECTOR, "a[class^=new-item-box__overlay]")
                # data['url'] = item_a.get_attribute('href').split('?')[0]
                # item_info = item_a.get_attribute('title')
                # split_idx = item_info.find('price')
                # last_comma_idx = item_info[:split_idx].rfind(',')
                # data['description'] = item_info[:split_idx][:last_comma_idx]
                # price_brand_size = {}
                # for kv in item_info[split_idx:].split(','):
                #     k, v = kv.split(':')
                #     k = k.strip()
                #     v = v.strip()
                #     price_brand_size[k] = v
                #     if k == 'price':
                #         data['price'] = v
                #     elif k == 'brand':
                #         data['brand'] = v
                #     elif k == 'size':
                #         data['size'] = v

                # I don't know why the fuck vinted has different data-testid for ordinary items and closet items
                item_title_p = item_div.find_element(By.CSS_SELECTOR, f"p[data-testid$='{data['id']}--description-title']")
                item_subtitle_p = item_div.find_element(By.CSS_SELECTOR, f"p[data-testid$='{data['id']}--description-subtitle']")
                item_price_p = item_div.find_element(By.CSS_SELECTOR, f"p[data-testid$='{data['id']}--price-text']")

                if item_title_p is not None:
                    data['title'] = item_title_p.text
                if item_subtitle_p is not None:
                    data['subtitle'] = item_subtitle_p.text
                if item_price_p:
                    data['price'] = item_price_p.text

                # TODO: item.owner
                item = SpiderItem(task_id=task.task_id)
                item.data = data
                items.append(item)

        return items

    def _scroll_down_randomly(self):
        times = random.randint(5, 8)
        for _ in range(times):
            delay = random.uniform(1, 2)
            sleep(delay)
            amount = random.randint(800, 1200)
            self.browser.scroll_down(amount)

    def _goto_next_page(self):
        self.browser.click_on("a[data-testid=catalog-pagination--next-page]")

    def _wait_content(self):
        self.browser.wait_for("section[class=content-container]", to_be=ElementState.Present)

    def _close_domain_popup(self):
        self.browser.click_on("button[data-testid=domain-select-modal-close-button]")

    def _close_cookie_popup(self):
        self.browser.click_on("button[id=onetrust-reject-all-handler]")



__all__ = [
    'VintedSearchSpider'
]


if __name__ == "__main__":
    task = SpiderTask(
        urls=["https://www.vinted.com/catalog?search_text=earring"],
        max_items=100,
        max_pages=1,
    )

    spider = VintedSearchSpider()
    spider.submit(task)
    spider.run()
