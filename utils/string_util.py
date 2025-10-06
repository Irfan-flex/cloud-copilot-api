# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

import re
import os
from dotenv import load_dotenv
from datetime import datetime
from werkzeug.exceptions import BadRequest

load_dotenv()


def str_lower(input_string: str) -> str:
    """
    Convert a string to lowercase.

    Args:
        string (str): The input string.

    Returns:
        str: The lowercase version of the input string.
    """
    if not input_string:
        return input_string
    return input_string.lower()


def parse_cors_origins(cors_origins_string: str) -> list:
    """
    Parse a string of CORS origins into a list.

    Args:
        cors_origins_string (str): String of CORS origins, possibly comma-separated and enclosed in brackets.

    Returns:
        list: A list of origins.
    """
    if not cors_origins_string:
        return []
    cors_origins_string = cors_origins_string.strip('[]')
    return [origin.strip() for origin in cors_origins_string.split(',') if origin.strip()]


def parse_valid_date(date_str: str, fmt: str = '%d-%m-%Y') -> datetime:
    """
    Validates and parses a date string using the given format.

    Args:
        date_str (str): The date string to validate and parse.
        fmt (str): The expected date format (default is 'dd-mm-yyyy').

    Returns:
        datetime: The parsed datetime object.

    Raises:
        ValueError: If the date string does not match the expected format.
    """
    try:
        return datetime.strptime(date_str, fmt)
    except ValueError as e:
        raise BadRequest(f"Invalid date format. Expected format: '{fmt}'.") from e
    
def validate_date_range(start_date: datetime, end_date: datetime, max_days: int = 60) -> None:
    """
    Validates that the date range is valid and does not exceed the specified limit.

    Args:
        start_date (datetime): The start of the date range.
        end_date (datetime): The end of the date range.
        max_days (int): Maximum allowed range in days (default is 60).

    Raises:
        ValueError: If start_date > end_date or range exceeds max_days.
    """
    if start_date > end_date:
        raise BadRequest("start_date cannot be after end_date")

    if (end_date - start_date).days > max_days:
        raise BadRequest(f"Date range cannot exceed {max_days} days")