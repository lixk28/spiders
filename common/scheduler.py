import multiprocessing

from multiprocessing import Pool, Queue
from common.documents import SpiderTask, SpiderItem
from common.spiders import Spider
from common.browser import Browser

class Scheduler:
    def __init__(self, process_num: int = 4):
        self.process_pool = multiprocessing.Pool()
        self.task_queue = multiprocessing.Queue()

    def submit(self, task: SpiderTask):
        self.task_queue.put(task)

    def execute_one(self):
        task: SpiderTask = self.task_queue.get()
        browser = Browser()
        spider = Spider(browser=browser)

        for i, item in enumerate(spider.scrape(task)):
            pass
