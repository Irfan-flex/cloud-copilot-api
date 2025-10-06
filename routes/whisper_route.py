# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

"""
This module provides functionality for performing searches on an index 
by using the provdied configuration.
"""

import logging
from flask import Blueprint, abort, request, Response
from services.whisper_service import transcribe
from datetime import datetime
from middlewares.auth_middleware import authorize

logger = logging.getLogger(__name__)

# Property key's sent in the query params
Q_QUERYPARAM_KEY = 'q'
MAX_AUDIO_SIZE = 5 * 1024 * 1024  # 5 MB

whisper_blueprint = Blueprint('whisper', __name__)

@whisper_blueprint.route('/whisper/transcribe', methods=['POST'])
@authorize(required=False)
def transcribe_route():
    """
    Endpoint to handle audio file upload and transcribe it using a transcription service.

    This route accepts a POST request with an audio file. It processes the file and 
    returns the transcribed text.

    Returns:
        dict: A JSON response containing the transcribed text or an error message.
        status code: 200 if transcription is successful, 400 or 500 for errors.
    """
    if request.content_length and request.content_length > MAX_AUDIO_SIZE:
        abort(413, f"Audio file too large. Maximum allowed size is 5 MB.")

    audio_file = request.files.get("file")
    if not audio_file:
                abort(400, f"Request does not contain an audio file, please provide an audio file in the file field")
        
    try:
        result=  transcribe(audio_file)
        logger.info("Transcription complete: %s",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))

        return {"text": result["text"]}, 200

    except RuntimeError as e:
        logger.error("Transcription API Error: %s", str(e))
        return {"error": str(e)}, 500

    except Exception as e:
        logger.critical("Unexpected API error: %s", str(e))
        return {"error": "Internal Server Error"}, 500