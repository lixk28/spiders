import sys
import time
import asyncio
import logging
import random
import traceback
from inspect import getsourcefile, getsourcelines

from functools import wraps, partial
from typing import Optional, Callable


class RetryPolicy:
    def __init__(self, max_retries: int = 3, max_timeout: float = 32):
        self._max_retries = max_retries
        self._max_timeout = max_timeout

    @property
    def max_retries(self) -> int:
        return self._max_retries

    @property
    def max_timeout(self) -> float:
        return self._max_timeout

    def next_delay(self) -> float:
        raise NotImplementedError('next_delay must be implemented by subclasses')

    def __str__(self):
        fmt = f"{self.__class__.__name__}(\n"
        for i, var in enumerate(vars(self)):
            fmt += f"\t{var}={getattr(self, var)},\n"
        fmt += ")"
        return fmt


# 线性退避 (固定间隔)
class LinearBackoffRetryPolicy(RetryPolicy):
    def __init__(self, max_retries: int = 3, max_timeout: float = 32, retry_interval = 5):
        super().__init__(max_retries, max_timeout)
        self.retry_interval = retry_interval

    def next_delay(self) -> float:
        return self.retry_interval


# 随机退避 (随机间隔)
class RandomBackoffRetryPolicy(RetryPolicy):
    def __init__(self, max_retries: int = 3, max_timeout: float = 32, min_retry_interval: float = 1, max_retry_interval: float = 5):
        super().__init__(max_retries, max_timeout)
        self.min_retry_interval = max(min_retry_interval, 0)
        self.max_retry_interval = min(max_retry_interval, max_timeout)

    def next_delay(self) -> float:
        return random.random(self.min_retry_interval, self.max_retry_interval)


# 指数退避
class ExponentialBackoffRetryPolicy(RetryPolicy):
    def __init__(self, max_retries: int = 3, max_timeout: float = 32, initial_interval: float = 1, base: int = 2):
        super().__init__(max_retries, max_timeout)
        self.curr_interval = min(initial_interval, max_timeout)
        self.base = base

    def next_delay(self) -> float:
        interval = self.curr_interval + random.uniform(0, 3)
        self.curr_interval = self.curr_interval * self.base
        return interval


def _fmt_func_info(func: Callable) -> str:
    return f"{func.__module__} :: {func.__name__} => {getsourcefile(func)}:{getsourcelines(func)[1]}"


class RetryError(Exception):
    def __init__(self, msg: str, *, func: Callable, retry_policy: RetryPolicy):
        self.msg = msg
        self.func = func
        self.policy = retry_policy

    def __str__(self):
        return f"[{self.__class__.__name__}] {_fmt_func_info(self.func)} retry_policy={self.policy}: {self.msg}"


# 失败重试装饰器，只可用来装饰同步方法，默认指数退避
def retry(
    func: Callable = None,
    *,
    retry_policy: RetryPolicy = ExponentialBackoffRetryPolicy(
        max_retries = 3,
        max_timeout = 32,
        initial_interval = 1,
        base = 2
    ),
    logger: logging.Logger = logging.getLogger(),
    reraise: bool = False,
    on_retry: Optional[Callable[[int, Exception], None]] = None):

    if func is None:
        return partial(retry, retry_policy=retry_policy, logger=logger, on_retry=on_retry)

    if not (isinstance(logger, logging.Logger) or hasattr(logger, 'error') and callable(logger.error)):
        raise TypeError(f"{func.__name__} {logger} is not a logging.Logger or does not implement error() method")

    max_retries = retry_policy.max_retries
    max_timeout = retry_policy.max_timeout

    @wraps(func)
    def wrapper(*args, **kwargs):
        attempt = 1
        last_exc = None
        while attempt <= max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if on_retry:
                    on_retry(attempt, e)
                delay = retry_policy.next_delay()
                delay = min(delay, max_timeout)
                logger.error(f"[{_fmt_func_info(func)}] attempt {attempt}/{max_retries} failed, retry in {delay} seconds: {e}")
                time.sleep(delay)
            attempt += 1

        if reraise:
            raise last_exc
        else:
            raise RetryError(f"Max retries ({max_retries}) exceeded", func=func, retry_policy=retry_policy) from last_exc

    return wrapper


# 异步失败重试装饰器
def async_retry(
    func: Callable = None,
    *,
    retry_policy: RetryPolicy = ExponentialBackoffRetryPolicy(
        max_retries = 3,
        max_timeout = 32,
        initial_interval = 1,
        base = 2
    ),
    logger: logging.Logger = logging.getLogger(),
    reraise: bool = False,
    on_retry: Optional[Callable[[int, Exception], None]] = None):

    if func is None:
        return partial(async_retry, retry_policy=retry_policy, logger=logger, on_retry=on_retry)

    if not asyncio.iscoroutinefunction(func):
        raise TypeError(f"{func.__name__} is not a coroutine function")

    if not (isinstance(logger, logging.Logger) or hasattr(logger, 'error') and callable(logger.error)):
        raise TypeError(f"{func.__name__} {logger} is not a logging.Logger or does not implement error() method")

    max_retries = retry_policy.max_retries
    max_timeout = retry_policy.max_timeout

    @wraps(func)
    async def wrapper(*args, **kwargs):
        attempt = 1
        last_exc = None
        while attempt <= max_retries:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if on_retry:
                    on_retry(attempt, e)
                delay = retry_policy.next_delay()
                delay = min(delay, max_timeout)
                logger.error(f"[{_fmt_func_info(func)}] attempt {attempt}/{max_retries} failed, retry in {delay} seconds: {e}")
                await asyncio.sleep(delay)
            attempt += 1

        if reraise:
            raise last_exc
        else:
            raise RetryError(f"Max retries ({max_retries}) exceeded", func=func, retry_policy=retry_policy) from last_exc

    return wrapper
