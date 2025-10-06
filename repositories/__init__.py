"""
 Copyright Flexday Solutions LLC, Inc - All Rights Reserved
 Unauthorized copying of this file, via any medium is strictly prohibited
 Proprietary and confidential
 See file LICENSE.txt for full license details.
"""

import gevent
from services.logging_service import logging
from repositories import (
    chat_analytics_repository, chat_session_repository)


logger = logging.getLogger(__name__)


def create_indexes():
    """
    Create indexes on the MongoDB collections.

    This function initializes the creation of indexes for various MongoDB collections 
    by calling the `create_index` method on different repository objects. It ensures 
    that the required indexes are set up for efficient querying and data retrieval.

    The collections being indexed:
        - Chatbot Template

    Logs:
        A debug message indicating successful creation of indexes.
    """

    # List of greenlets (tasks) to run concurrently
    greenlets = [
        gevent.spawn(chat_session_repository.create_index),
        gevent.spawn(chat_analytics_repository.create_index)
    ]

    # Wait for all greenlets to complete
    gevent.joinall(greenlets)

    for greenlet in greenlets:
        if greenlet.exception:
            # Handle exceptions if any
            raise greenlet.exception

    logger.debug("Indexes created successfully for Database collections")


create_indexes()
