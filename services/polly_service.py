# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

import boto3
import os
import uuid
import logging
import html
from botocore.exceptions import BotoCoreError, ClientError

AUDIO_DIR = "tts_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

polly_client = boto3.client("polly")

def synthesize_speech(text: str, speed: float = 1.0) -> str:
    if not text.strip():
        raise ValueError("Text is empty or invalid.")

    text = html.unescape(text)

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    # Adjust speed using SSML
    rate_percent = f"{int(speed * 100)}%"
    ssml_text = f"<speak><prosody rate='{rate_percent}'>{text}</prosody></speak>"

    try:
        response = polly_client.synthesize_speech(
            TextType="ssml",
            Text=ssml_text,
            OutputFormat="mp3",
            VoiceId="Joanna"
        )

        with open(filepath, "wb") as f:
            f.write(response["AudioStream"].read())

        return filepath

    except (BotoCoreError, ClientError) as e:
        logging.error("Amazon Polly synthesis error: %s", str(e))
        raise RuntimeError("Amazon Polly failed to synthesize speech.") from e
    

def validate_speed(value):
    """
    Validate the 'speed' parameter.

    Args:
        value: The input speed value (could be None, str, float, etc.)

    Returns:
        float: Validated speed value between 0.1 and 2.0 inclusive.

    Raises:
        ValueError: If the value is not a number or out of allowed range.
    """
    default_speed = 1.0
    min_speed = 0.1
    max_speed = 2.0

    if value is None:
        return default_speed

    try:
        speed = float(value)
    except (TypeError, ValueError):
        raise ValueError("Speed must be a number.")

    if not (min_speed <= speed <= max_speed):
        raise ValueError(f"Speed must be between {min_speed} and {max_speed}.")

    return speed
