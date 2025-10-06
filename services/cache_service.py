"""
Module for cache management.

Copyright Flexday Solutions LLC, Inc - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
See file LICENSE.txt for full license details.
"""

import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)
CACHE_TTL_DAYS = 7

store: Dict[str, Any] = {}


def init_cache() -> None:
    """
    Initializes the cache by creating an empty dictionary called "store".
    """
    global store
    store = {}
    logger.info("Cache created...")


def clear_all() -> None:
    """
    Clears all elements in the cache.
    """
    store.clear()
    logger.info("Cache cleared...")


def set(key: str, value: Any) -> None:
    """
    Stores value in cache along with the current timestamp.
    """
    store[key] = {
        "value": value,
        "timestamp": datetime.utcnow()
    }
    logger.info("Set value in cache for key: %s", key)


def get(key: str) -> Any:
    """
    Retrieves value from cache if it hasn't expired.
    """
    item = store.get(key)
    if not item:
        logger.info("Cache miss for key: %s", key)
        return None

    timestamp = item.get("timestamp")
    if not timestamp or (datetime.utcnow() - timestamp) > timedelta(days=CACHE_TTL_DAYS):
        logger.info("Cache expired for key: %s", key)
        # Clear only if key is 'top_news'
        if key == "top_news":
            store.pop(key, None)  # Optional: remove expired cache
            logger.info("Cleared expired cache for key: %s", key)
        return None

    logger.info("Cache hit for key: %s", key)
    return item["value"]


def get_all_keys() -> List[str]:
    """
    Returns a list of all the keys in the cache.

    :return: List[str]
        A list of all the keys in the cache.
    """
    keys = store.keys()
    return list(keys)