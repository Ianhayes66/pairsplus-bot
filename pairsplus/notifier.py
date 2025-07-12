"""
pairsplus/notifier.py

Sends messages to Discord webhook for monitoring.
"""


import logging
import requests
from .config import DISCORD_WEBHOOK_URL

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def send_discord_message(content: str):
    """
    Posts a message to Discord via webhook.
    """
    if not DISCORD_WEBHOOK_URL or not DISCORD_WEBHOOK_URL.strip():
        logger.warning("[Notifier] No DISCORD_WEBHOOK_URL set. Skipping message.")
        return

    payload = {"content": content}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code == 204:
            logger.info("[Notifier] Message sent to Discord successfully.")
        else:
            logger.error(
                f"[Notifier] Discord webhook error: {response.status_code} {response.text}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"[Notifier] Exception sending Discord message: {e}")
