# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

import traceback
import logging
from flask import Blueprint
from constants import EXCEPTION_HTTP_STATUS_CODE, EXCEPTION_HTTP_STATUS_TYPE
from werkzeug.exceptions import HTTPException
from utils.env_config import APP_CONFIG

logger = logging.getLogger(__name__)

errorHandler = Blueprint('errorHandler', __name__)


@errorHandler.app_errorhandler(HTTPException)
def handle_exception(exc: HTTPException):
    """
    Handle HTTPException errors and return JSON responses instead of HTML.

    The function `handle_exception` returns a JSON object containing information about an HTTP error,
    including the error code, type, and message.
    
    :param exc: HTTPException,
      exception that occurred during the handling of an HTTP request
    :return: Tuple (JSON response, HTTP status code)
    """

    logger.exception(exc)

    error_body = {
        "code": exc.code,
        "type": exc.name,
        "message": exc.description,
    }
    if APP_CONFIG.DEBUG:
        error_body["stacktrace"] = "".join(
            traceback.TracebackException.from_exception(exc).format())

    return error_body, exc.code


@errorHandler.app_errorhandler(Exception)
def handle_exception(exc: Exception):
   
    """
    Returns a structured JSON response for generic/unhandled exceptions.

    The function `handle_exception` returns a JSON object containing information about an HTTP error,
    including the error code, type, and message.
    
    :param exc: Exception,
      exception that occurred during the handling of an HTTP request
    :return: Tuple (JSON response, HTTP status code)
    """

    logger.exception(exc)

    error_body = {
        "code": EXCEPTION_HTTP_STATUS_CODE,
        "type": EXCEPTION_HTTP_STATUS_TYPE,
        "message": str(exc),
    }
    if APP_CONFIG.DEBUG:
        error_body["stacktrace"] = "".join(
            traceback.TracebackException.from_exception(exc).format())

    return error_body, EXCEPTION_HTTP_STATUS_CODE
