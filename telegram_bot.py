# telegram_bot.py
import logging
import os
import uuid
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

from config import (TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_USER_ID, ENABLE_LOGGING, 
                    LOG_FILE, TEMP_DIR)
from commands.ai_chat import GeminiClient
from commands.agent import think
from commands.image_tools import analyze_image_content
from commands.voice_tools import transcribe_audio

# --- Logger Setup ---
if ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(LOG_FILE, encoding='utf-8'),
                            logging.StreamHandler()
                        ])
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

# Global GeminiClient instance
gemini_client = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm your AI CLI Assistant bot. \n"
        "You can send me a task as a text message, a voice message, or an image with a caption."
    )
    logger.info(f"User {user.username} (ID: {user.id}) started the bot.")

async def process_agent_request(update: Update, context: ContextTypes.DEFAULT_TYPE, user_goal: str):
    """A helper function to run the agent and handle its output."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if not gemini_client:
        await update.message.reply_text("Error: AI client is not initialized. Please check bot logs.")
        logger.error("GeminiClient is None in process_agent_request.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    try:
        final_agent_output = think(gemini_client, user_goal, user_id=user_id)
        
        if not final_agent_output:
            await update.message.reply_text("Agent completed the task, but no specific output was generated.")
            logger.info(f"Agent task completed for chat ID: {chat_id} with no output.")
            return

        # Check if the agent produced a voice message
        if final_agent_output.endswith('.mp3') and os.path.exists(final_agent_output):
            logger.info(f"Sending voice response: {final_agent_output}")
            await context.bot.send_voice(chat_id=chat_id, voice=open(final_agent_output, 'rb'))
            os.remove(final_agent_output) # Clean up the temp audio file
        else:
            # Send as text, splitting if necessary
            if len(final_agent_output) > 4096:
                for i in range(0, len(final_agent_output), 4096):
                    await update.message.reply_text(final_agent_output[i:i+4096], parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(final_agent_output, parse_mode=ParseMode.HTML)
        
        logger.info(f"Agent task completed successfully for chat ID: {chat_id}.")

    except Exception as e:
        logger.error(f"Error running agent task for goal '{user_goal}': {e}", exc_info=True)
        await update.message.reply_text(f"Sorry, the agent encountered an error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes incoming text messages by passing them to the agent."""
    user_message = update.message.text
    username = update.effective_user.username or update.effective_user.full_name
    logger.info(f"Received text message from {username} (ID: {update.effective_user.id}): {user_message}")

    if not user_message.strip():
        await update.message.reply_text("Please provide a message for the agent to work on.")
        return
        
    await process_agent_request(update, context, user_message)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Analyzes a received photo."""
    username = update.effective_user.username or update.effective_user.full_name
    logger.info(f"Received photo from {username} (ID: {update.effective_user.id})")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")

    file_id = update.message.photo[-1].file_id
    new_file = await context.bot.get_file(file_id)
    
    # Create a temporary file path
    file_name = f"{uuid.uuid4()}.jpg"
    temp_file_path = os.path.join(TEMP_DIR, file_name)
    
    await new_file.download_to_drive(temp_file_path)
    logger.info(f"Photo downloaded to {temp_file_path}")

    # The user's caption is used as the prompt for the image analysis
    prompt = update.message.caption
    if not prompt:
        # If no caption, use a default analysis type
        analysis_result = analyze_image_content(file_path=temp_file_path, analysis_type='describe')
    else:
        # If there is a caption, use it as a custom prompt
        analysis_result = analyze_image_content(file_path=temp_file_path, custom_prompt=prompt)
        
    await update.message.reply_text(analysis_result)
    
    # Clean up the downloaded file
    os.remove(temp_file_path)
    logger.info(f"Cleaned up temporary photo: {temp_file_path}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Transcribes a received voice message and passes it to the agent."""
    username = update.effective_user.username or update.effective_user.full_name
    logger.info(f"Received voice message from {username} (ID: {update.effective_user.id})")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    file_id = update.message.voice.file_id
    new_file = await context.bot.get_file(file_id)

    # Download the voice message (Telegram uses .oga format)
    file_name = f"{uuid.uuid4()}.oga"
    temp_file_path = os.path.join(TEMP_DIR, file_name)
    await new_file.download_to_drive(temp_file_path)
    logger.info(f"Voice message downloaded to {temp_file_path}")

    # Transcribe the audio
    transcribed_text = transcribe_audio(audio_file_path=temp_file_path)

    # Clean up the downloaded file
    os.remove(temp_file_path)
    logger.info(f"Cleaned up temporary voice file: {temp_file_path}")

    if transcribed_text.startswith("Error:"):
        await update.message.reply_text(f"Could not process the voice message. {transcribed_text}")
        return

    await update.message.reply_text(f"Transcribed Text: \"{transcribed_text}\"\n\nNow, let me think about that...")
    
    # Pass the transcribed text to the agent
    await process_agent_request(update, context, transcribed_text)

def main() -> None:
    """Starts the Telegram bot."""
    global gemini_client
    
    try:
        gemini_client = GeminiClient()
        logger.info("GeminiClient initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize GeminiClient: {e}. Bot cannot start.")
        return

    if not TELEGRAM_BOT_TOKEN or "YOUR_TELEGRAM_BOT_TOKEN" in TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN is not set in config.py or environment variables.")
        return
    
    if TELEGRAM_ADMIN_USER_ID == 919340565: # Using the placeholder from the file
        logger.warning("TELEGRAM_ADMIN_USER_ID is not set to a custom value. Shell commands will be disabled via Telegram.")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
 
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))


    logger.info("Starting Telegram bot polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram bot stopped.")

if __name__ == "__main__":
    main()