import logging
import sys

from envparse import env
from loguru import logger


env.read_envfile(".env")


class InterceptHandler(logging.Handler):
    """Logger handler to intercept standard logger messages."""

    def emit(self, record: logging.LogRecord) -> None:
        """Reemit the message via loguru.logger."""
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:  # pragma: no cover
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


logging.basicConfig(handlers=[InterceptHandler()], level=0)

logger.remove()
logger.add(sys.stderr, level="DEBUG" if env.bool("WLB_DEBUG") else "INFO")
