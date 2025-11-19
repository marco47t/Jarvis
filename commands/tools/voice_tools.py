# commands/tools/voice_tools.py
import time
import logging
import uuid
from pathlib import Path
import google.generativeai as genai
from google.cloud import texttospeech

from config import ENABLE_LOGGING, GEMINI_API_KEY

if ENABLE_LOGGING:
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

def _configure_genai():
    """Configures the Generative AI client."""
    if not GEMINI_API_KEY or "YOUR_GOOGLE_GEMINI_API_KEY" in GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in config.py or environment variables.")
    genai.configure(api_key=GEMINI_API_KEY)


# VVV THIS IS THE FUNCTION THAT WAS ACCIDENTALLY DELETED. IT IS NOW RESTORED. VVV
def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribes audio from a file using the Gemini Pro model.

    Args:
        audio_file_path (str): The local path to the audio file.

    Returns:
        str: The transcribed text or an error message.
    """
    try:
        _configure_genai()
        logger.info(f"Uploading audio file for transcription: {audio_file_path}")
        
        # This assumes webm format from the frontend recorder
        audio_file = genai.upload_file(path=audio_file_path, mime_type="audio/webm")
        
        logger.info("Waiting for audio file to be processed...")
        while audio_file.state.name == "PROCESSING":
            time.sleep(2) # Check every 2 seconds
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED":
            logger.error(f"Google file processing failed for transcription.")
            return f"Error: Audio file processing failed."
            
        logger.info(f"Audio file processed successfully.")
        
        # Use a model that supports multimodal input
        model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
        
        prompt = "Transcribe the following audio recording precisely. Provide only the text of the speech."
        
        response = model.generate_content([prompt, audio_file])
        
        transcribed_text = response.text.strip()
        logger.info("Audio transcription successful.")
        return transcribed_text

    except Exception as e:
        logger.error(f"An unexpected error occurred during audio transcription: {e}", exc_info=True)
        return f"Error: An unexpected error occurred during audio transcription. Details: {e}"


# VVV THIS IS YOUR NEW, SIMPLIFIED TEXT-TO-SPEECH FUNCTION VVV
def text_to_speech(text_to_synthesize: str, output_directory: str = 'web/audio') -> str:
    """
    Synthesizes text into a high-quality MP3 audio file using Google Cloud TTS.
    This is a simplified version that does not handle timestamps.

    Args:
        text_to_synthesize (str): The plain text content to be converted to speech.
        output_directory (str): The directory where the output MP3 file will be saved.

    Returns:
        str: The absolute path to the generated MP3 file or an error string on failure.
    """
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text_to_synthesize)

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-AU",
            name="en-AU-Wavenet-D",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.95
        )

        print("--- DEBUG: Sending request to Google TTS API... ---")
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        print("--- DEBUG: Received audio response from Google TTS API. ---")

        output_path_obj = Path(output_directory)
        output_path_obj.mkdir(parents=True, exist_ok=True)
        
        output_filename = f"briefing_{uuid.uuid4()}.mp3"
        file_path = output_path_obj / output_filename

        with open(file_path, "wb") as out:
            out.write(response.audio_content)
            logger.info(f'Generated speech and saved to "{file_path}"')

        return {"status": "success", "audio_path": str(file_path.resolve())}

    except Exception as e:
        logger.error(f"Google TTS Error: {e}", exc_info=True)
        # On failure, return a dictionary
        return {"status": "error", "error": f"Failed to synthesize speech. Details: {e}"}