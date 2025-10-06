# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.


import logging
import os
from flask import Blueprint, request, send_file, jsonify, after_this_request
from services.polly_service import synthesize_speech, validate_speed
from middlewares.auth_middleware import authorize

logger = logging.getLogger(__name__)
polly_blueprint = Blueprint("gtts", __name__)

@polly_blueprint.route("/tts/synthesize", methods=["POST"])
@authorize(required=False)
def synthesize_route():
    """
    Endpoint to synthesize speech using Amazon Polly from provided text.

    Expects a JSON payload with:
      - text (str): required
      - speed (float): optional (default = 1.0)

    Returns:
        MP3 audio file.
    """
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing required 'text' field"}), 400

    text = data["text"]
    try:
        speed = validate_speed(data.get("speed"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        audio_path = synthesize_speech(text, speed)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(audio_path)
            except Exception as e:
                logger.warning(f"Could not delete temp file {audio_path}: {e}")
            return response

        return send_file(audio_path, mimetype="audio/mpeg", as_attachment=False)

    except ValueError as ve:
        logger.warning("TTS Input Error: %s", ve)
        print(ve)
        return jsonify({"error": str(ve)}), 400

    except RuntimeError as re:
        logger.error("Polly Runtime Error: %s", re)
        print(re)
        return jsonify({"error": str(re)}), 500

    except Exception as e:
        logger.error("TTS Generation Unexpected Error: %s", e, exc_info=True)
        print(e)
        return jsonify({"error": "Unexpected error occurred during TTS synthesis."}), 500
