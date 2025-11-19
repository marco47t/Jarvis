# commands/voice_tools.py
import time
import logging
import uuid
import pyttsx3
from pathlib import Path
import google.generativeai as genai

# Re-add the config import and original logger setup
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

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribes audio from a file using the Gemini Pro model.
    This approach uses the file API directly, which avoids local dependencies.

    Args:
        audio_file_path (str): The local path to the audio file.

    Returns:
        str: The transcribed text or an error message.
    """
    try:
        _configure_genai()
        logger.info(f"Uploading audio file for transcription via Gemini API: {audio_file_path}")
        
        # Upload the file with the correct mime type
        audio_file = genai.upload_file(path=audio_file_path, mime_type="audio/webm")
        
        logger.info("Waiting for file to be processed by Google...")
        while audio_file.state.name == "PROCESSING":
            print('.', end='', flush=True)
            time.sleep(5) # Check every 5 seconds
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED":
            logger.error(f"Google file processing failed.")
            return f"Error: Google's file processing failed. The file may be invalid or the API is experiencing issues."
            
        logger.info(f"File processed successfully. Display name: {audio_file.display_name}")
        
        # IMPORTANT: Use the Gemini 1.5 Pro model for this task, as it's built for multimodal input.
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
        prompt = "Transcribe the following audio recording precisely. Provide only the text of the speech."
        
        response = model.generate_content([prompt, audio_file])
        
        transcribed_text = response.text.strip()
        logger.info("Audio transcription successful.")
        return transcribed_text

    except Exception as e:
        logger.error(f"An unexpected error occurred during Gemini audio transcription: {e}", exc_info=True)
        return f"Error: An unexpected error occurred during audio transcription. Details: {e}"

def text_to_speech(text_to_synthesize: str, output_directory: str = 'audio_responses') -> str:
    """
    Synthesizes text into an audio file using a local TTS engine (pyttsx3).
    This function remains unchanged.
    """
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id) 
        rate = engine.getProperty('rate')
        engine.setProperty('rate', rate + 20)
        output_path_obj = Path(output_directory)
        output_path_obj.mkdir(parents=True, exist_ok=True)
        output_filename = f"{uuid.uuid4()}.mp3"
        file_path = output_path_obj / output_filename
        engine.save_to_file(text_to_synthesize, str(file_path))
        engine.runAndWait()
        return str(file_path)
    except Exception as e:
        logger.error(f"An unexpected error occurred during text-to-speech synthesis: {e}", exc_info=True)
        return f"Error: An unexpected error occurred during speech synthesis. Details: {e}"