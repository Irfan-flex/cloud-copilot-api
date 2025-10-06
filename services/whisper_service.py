# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

from utils.storage_util import delete_path, join_path, get_file_name_from_path, path_exists
from werkzeug.utils import secure_filename
import whisper
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Load Whisper model (You can change to 'base', 'small', 'medium' etc.)
model = whisper.load_model("base")

def is_valid_webm(file_path):
    """
    Validates WebM file using ffprobe. Returns True if format and streams are intact.
    Logs success and failure clearly.
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("✅ Valid WebM file: %s", file_path)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("❌ Invalid WebM file: %s", file_path)
        logger.error("ffprobe error: %s", e.stderr.strip())
        return False


def transcribe(audio_file):
    """
    Transcribe an audio file using Whisper, saving the file temporarily.
    
    :param audio_file: A FileStorage object from Flask (e.g., request.files['file'])
    :return: The transcription result from the Whisper model.
    """
    logger.info("Inside transcribe function at: %s",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))

    try:
        # Ensure the "audios" directory exists
        audio_dir = "audios"

        filename = secure_filename(audio_file.filename)
        file_full_path = join_path(audio_dir, filename)

        # Save the uploaded file
        audio_file.save(file_full_path)
        logger.info("File saved at path: %s at: %s",
            file_full_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
        

        # Check if file has a valid EBML header
        if not is_valid_webm(file_full_path):
            delete_path(file_full_path)
            raise RuntimeError("Invalid WebM file. Possibly corrupted or incomplete.")


        # Transcribe the audio
        try:
            result = model.transcribe(file_full_path, fp16=False)
            logger.info("Model transcription completed successfully at: %s",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))

        except Exception as transcribe_err:
            logger.error("Error during transcription: %s at: %s",
                str(transcribe_err), datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
            raise RuntimeError(f"Transcription failed: {str(transcribe_err)}") from transcribe_err

        finally:
            # Cleanup the file, even if transcription fails
            if path_exists(file_full_path):
                delete_path(file_full_path)
                logger.info("Temporary file deleted: %s", file_full_path)

        return result

    except Exception as e:
        logger.error("Unexpected error in transcribe function: %s at: %s",
            str(e), datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
        raise RuntimeError(f"An error occurred during transcription: {str(e)}") from e
