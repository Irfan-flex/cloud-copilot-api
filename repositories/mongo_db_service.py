# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

import time
from pymongo import MongoClient
from utils.env_config import DB_CONFIG
from datetime import datetime, timezone
import logging

logging.getLogger("pymongo").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


CREATED_AT_FIELD_NAME = "createdAt"
LAST_UPDATED_AT_FIELD_NAME = "lastUpdatedAt"
UNDERSCORE_ID_FIELD_NAME = "_id"
ID_FIELD_NAME = "id"

start_time = time.time()
client = MongoClient(DB_CONFIG.MONGODB_HOST_URI,
                     maxPoolSize=DB_CONFIG.MONGODB_MAX_POOLSIZE, 
                     minPoolSize=DB_CONFIG.MONGODB_MIN_POOLSIZE,
                     maxIdleTimeMS=DB_CONFIG.MONGODB_MAX_IDLETIME_MS,
                     maxConnecting=DB_CONFIG.MONGODB_MAX_CONNECTING)

client.admin.command("ping")
end_time = time.time()
elapsed_time_ms = round((end_time - start_time) * 1000, 2)
logger.info(f"MongoDB client connected successfully in {elapsed_time_ms} ms")

def get_database():
    """
    Retrieves the MongoDB database client connection based on the configuration.

    Returns:
        Database: The MongoDB database instance specified in DB_CONFIG.
    """
    return client[DB_CONFIG.MONGODB_DBNAME]

def generate_create_doc_with_audit_and_timestamp(doc, id=None):
    """
    Generates a document with audit fields and timestamps for creation.

    Args:
        doc (dict): The document to be created, which will be enriched with audit fields.
        id (str, optional): A custom ID to set for the document. Defaults to None.

    Returns:
        dict: The document with audit information, creation timestamp, and optional custom ID.
    """
    doc[CREATED_AT_FIELD_NAME] = generate_timestamp()
    doc[LAST_UPDATED_AT_FIELD_NAME] = generate_timestamp()
    if id:
        doc[UNDERSCORE_ID_FIELD_NAME] = id
    return doc

def generate_update_doc_with_timestamp(doc):
    """
    Generates an update document with an updated timestamp.

    Args:
        doc (dict): The document to be updated.

    Returns:
        dict: The document with the updated 'last_updated_at' field.
    """
    doc[LAST_UPDATED_AT_FIELD_NAME] = generate_timestamp()
    return doc

def generate_timestamp():
    """
    Generates the current timestamp in UTC timezone.

    This function retrieves the current local date and time, converts it to the UTC timezone,
    and returns the UTC datetime object.

    Returns:
    datetime: The current datetime in UTC timezone.
    """
    return datetime.now().astimezone(timezone.utc)

def format_timestamp(timestamp):
    """
    Converts a datetime object to a string in ISO 8601 format with UTC timezone information.

    This function checks if the provided timestamp is a valid datetime object. If it is,
    the timestamp is converted to UTC timezone and then formatted into a string in
    ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).

    Parameters:
    timestamp (datetime): The datetime object to be formatted.

    Returns:
    str: A string representing the formatted datetime in ISO 8601 format with UTC timezone,
         or None if the input is not a valid datetime object.
    """
    if timestamp and isinstance(timestamp, datetime):
        timestamp = timestamp.astimezone(timezone.utc)
        timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        return timestamp
    
def format_doc_with_id(doc):
    """
    Adds a string ID field to the document and removes the underscore ID field.

    Args:
        doc (dict): The document to format.

    Returns:
        dict: The document with an 'id' field (string representation of ObjectId) and without the 
              MongoDB internal '_id' field.
    """
    if not doc:
        return doc
    doc[ID_FIELD_NAME] = str(doc[UNDERSCORE_ID_FIELD_NAME])
    del doc[UNDERSCORE_ID_FIELD_NAME]
    return doc


def format_doc_with_timestamp(doc):
    """
    Formats the document by converting 'created_at' and 'last_updated_at' fields to ISO 8601 timestamp strings.

    Args:
        doc (dict): The document to format.

    Returns:
        dict: The document with formatted timestamp fields.
    """
    if not doc:
        return doc

    if CREATED_AT_FIELD_NAME in doc:
        doc[CREATED_AT_FIELD_NAME] = format_timestamp(
            doc[CREATED_AT_FIELD_NAME])

    if LAST_UPDATED_AT_FIELD_NAME in doc:
        doc[LAST_UPDATED_AT_FIELD_NAME] = format_timestamp(
            doc[LAST_UPDATED_AT_FIELD_NAME])
    return doc

def format_doc_with_id_and_timestamp(doc):
    """
    Formats the document by adding an 'id' field and formatting 'created_at' and 'last_updated_at' timestamp fields.

    Args:
        doc (dict): The document to format.

    Returns:
        dict: The document with both 'id' and formatted timestamp fields.
    """
    if not doc:
        return doc
    doc = format_doc_with_id(doc)
    doc = format_doc_with_timestamp(doc)
    return doc