from threading import Lock, RLock
from typing import Optional, List
from fake_useragent import UserAgent


# UA 池
class UserAgentPool:
    def __init__(self,
                 size: int = 2048,
                 browsers: Optional[List[str]] = [ 'firefox' ],
                 oses: Optional[List[str]] = [ 'linux' ],
                 platforms: Optional[List[str]] = [ 'desktop', 'mobile', 'tablet' ]):
        pass

    @property
    def random(self) -> str:
        pass
