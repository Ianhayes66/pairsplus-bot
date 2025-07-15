"""
pairsplus/notifier.py

Sends messages to Discord webhook for monitoring.
"""

import logging
import requests
from . import config

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

WEBHOOK_URL = config.DISCORD_WEBHOOK_URL

if not WEBHOOK_URL:
    logger.warning("[Notifier] DISCORD_WEBHOOK_URL is missing in environment. Discord notifications will be disabled.")

def send_discord_message(content: str):
    """
    Posts a message to Discord via webhook if configured.
    """
    if not WEBHOOK_URL:
        logger.debug("[Notifier] Skipping Discord send—no webhook URL.")
        return

    payload = {"content": content}
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code == 204:
            logger.info("[Notifier] Message sent to Discord successfully.")
        else:
            logger.error(
                f"[Notifier] Discord webhook error: {response.status_code} {response.text}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"[Notifier] Exception sending Discord message: {e}")