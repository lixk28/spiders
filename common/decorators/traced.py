import logging
import traceback

from functools import wraps

def exception_traced(logger=None, msg=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exc_msg = traceback.format_exc()
                if logger is not None:
                    logger.error(exc_msg)
                    logger.error(msg)
                else:
                    logging.error(exc_msg)
                    logging.error(msg)
                raise e
        return wrapper
    return decorator
