# pairsplus/logger.py

import logging
from .config import BASE_DIR

LOG_FILE = BASE_DIR / "bot.log"

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

handler_file = logging.FileHandler(LOG_FILE)
handler_file.setFormatter(formatter)

handler_console = logging.StreamHandler()
handler_console.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler_file, handler_console]
)

logger = logging.getLogger("pairsplus")