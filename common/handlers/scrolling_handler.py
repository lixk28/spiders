import random

from typing import Optional, Tuple
from abc import ABC, abstractmethod
from common.browser import Browser

class ScrollingHandler(ABC):
    def __init__(self, browser: Browser):
        self.browser = browser

    @abstractmethod
    def scroll_up(self):
        pass

    @abstractmethod
    def scroll_down(self):
        pass

    @abstractmethod
    def on_top(self):
        pass

    @abstractmethod
    def on_bottom(self):
        pass



class DefaultScrollingHandler(ScrollingHandler):
    def __init__(self,
                 browser: Browser,
                 scroll_scale: Optional[Tuple[float, float]]):
        super().__init__(browser)
        self.min_scrl_scale = float(scroll_scale[0])
        self.max_scrl_scale = float(scroll_scale[1])

    def scroll_up(self):
        wnd_h = self.browser.window_height
        min_scrl_step = int(wnd_h * self.min_scrl_scale)
        max_scrl_step = int(wnd_h * self.max_scrl_scale)
        scrl_step = random.randint(min_scrl_step, max_scrl_step)
        success = self.browser.scroll_up(scrl_step)
        return success

    def scroll_down(self):
        wnd_h = self.browser.window_height
        min_scrl_step = int(wnd_h * self.min_scrl_scale)
        max_scrl_step = int(wnd_h * self.max_scrl_scale)
        scrl_step = random.randint(min_scrl_step, max_scrl_step)
        success = self.browser.scroll_down(scrl_step)
        return success

    # called before scrolling starts
    def on_start(self):
        pass

    # called when scroll_up() reaches the top of the page
    def on_top(self):
        pass

    # called when scroll_down() reaches the bottom of the page
    def on_bottom(self):
        pass



__all__ = [
    'ScrollingHandler',
    'DefaultScrollingHandler',
]
