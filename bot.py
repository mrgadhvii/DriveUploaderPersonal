import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import time
import shutil
import threading



# Enable logging for debugging and monitoring
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration variables
BOT_TOKEN = "7508399265:AAHZcTfGFafKEhKNjeCISDfVqEyZ4jPHPsk"  # Replace with your actual token
SERVICE_ACCOUNT_FILE = r"C:\Users\User\Desktop\StudyMaterial\api\service-account.json"
OWNER_USERNAME = "@MrGadhvii"

# Initialize Google Drive API credentials and service
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
drive_service = build("drive", "v3", credentials=credentials)

# Folder IDs for upload options
FOLDER_OPTIONS = {
    "𝟭𝟭𝘁𝗵 𝗝𝗘𝗘": "1jWUbr_v4T_BlcTFuGDxzJqKfacxRN9Re",
    "𝟭𝟮𝘁𝗵 𝗝𝗘𝗘": "197NBp9QTxr9flCHBOKg0D3oXdvLo9dh0",
    "𝟭𝟭𝘁𝗵 𝗡𝗘𝗘𝗧": "1eYTDkkfnaPIkojyQALPUQBQfob9UNl0t",
    "𝟭𝟮𝘁𝗵 𝗡𝗘𝗘𝗧": "1Di_c6QYmfSI_uBvv0JQmxueEl9dEe84Z",
    "Dʀᴏᴘᴘᴇʀ Nᴇᴇᴛ": "10ipfp_W-_ld6qlebu7lqMs2vDOikA-M-"
}

# Handler for the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("Owner 😎", url="https://t.me/MrGadhvii")],
        [InlineKeyboardButton("Material Channel 📙", url="https://t.me/MyGSEB")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    greeting = (
        f"Hello, {user.first_name}!\n"
        f"<pre>Welcome to the 𝕄𝕒𝕥𝕖𝕣𝕚𝕒𝕝 𝕌𝕡𝕝𝕠𝕒𝕕 𝔹𝕠𝕥.</pre>\n\n"
        f"<b>Just Type /upload To Upload PDF into Website !</b>"
    )

    await update.message.reply_text(greeting, parse_mode="HTML")

# Handler for the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Welcome to the File Upload Bot! Here are the commands you can use:\n"
        "/start - Start the bot and get a greeting.\n"
        "/help - Get help with all available commands.\n"
        "/upload - Show folder options for file uploads.\n"
        "Use /upload to see the available folder options before uploading files."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# Handler for the /upload command to show folder options
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton(f"{key}", callback_data=f"select_{key}")] for key in FOLDER_OPTIONS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("𝘊𝘩𝘰𝘰𝘴𝘦 𝘢 𝘧𝘰𝘭𝘥𝘦𝘳 𝘁𝘰 𝘂𝘱𝘭𝘰𝘢𝘥 𝘺𝘰𝘶𝘳 𝘧𝘪𝘭𝘦𝘴​ :", reply_markup=reply_markup)

# Callback handler for folder selection
async def select_folder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        logger.error("Received a non-callback query event.")
        return

    await query.answer()  # Confirm the callback query

    # Extract the folder option from the callback data
    folder_option = query.data.split("_")[1]
    if folder_option in FOLDER_OPTIONS:
        context.user_data["selected_folder_id"] = FOLDER_OPTIONS[folder_option]
        await query.edit_message_text(f"You have chosen {folder_option} for file uploads.\n\n Now, 𝙨𝙚𝙣𝙙 𝙮𝙤𝙪𝙧 𝙋𝘿𝙁 𝙛𝙞𝙡𝙚 𝙩𝙤 𝙨𝙩𝙖𝙧𝙩 𝙪𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜.")
    else:
        await query.edit_message_text("Invalid selection. Please use /upload to choose a folder.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.document.mime_type == "application/pdf":
        selected_folder_id = context.user_data.get("selected_folder_id")
        if selected_folder_id:
            # Create a temporary directory for file storage
            temp_dir = f"./.tmp/{update.message.chat_id}"
            os.makedirs(temp_dir, exist_ok=True)

            # Save the PDF file locally
            file = await update.message.document.get_file()
            file_path = os.path.join(temp_dir, update.message.document.file_name)
            await file.download_to_drive(file_path)

            # Prepare file metadata and media for upload
            file_metadata = {"name": os.path.basename(file_path), "parents": [selected_folder_id]}
            media = MediaFileUpload(file_path, mimetype="application/pdf")
            request = drive_service.files().create(body=file_metadata, media_body=media, fields="id")

            try:
                # Upload the file
                request.execute()
                logger.info(f"Uploaded file: {file_path}")

                # Notify the user of successful upload
                await update.message.reply_text("File uploaded successfully! The temporary folder will now be deleted.")

                # Attempt to delete the temporary file with retry logic
                for attempt in range(3):  # Try up to 3 times
                    try:
                        os.remove(file_path)  # Remove the uploaded file
                        logger.info(f"Removed file: {file_path}")
                        break  # Exit the loop if successful
                    except OSError as e:
                        if e.winerror == 32:  # File is being used by another process
                            logger.warning(f"File is still in use, retrying... (Attempt {attempt + 1})")
                            time.sleep(1)  # Wait for 1 second before retrying
                        else:
                            logger.error(f"Error removing file: {e}")
                            break  # Exit the loop on other errors

                # Delete the temporary directory
                shutil.rmtree(temp_dir)  # Remove the temporary directory
                logger.info(f"Removed temporary directory: {temp_dir}")

            except Exception as e:
                logger.error(f"Error during file upload or deletion: {e}")
                await update.message.reply_text("An error occurred during the upload process.")
        else:
            await update.message.reply_text("You need to select a folder first using /upload.")
    else:
        await update.message.reply_text("Only PDF files are allowed!")
# Main function to set up the bot
def main() -> None:
    # Create the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("upload", upload))
    application.add_handler(CallbackQueryHandler(select_folder, pattern="^select_"))
    application.add_handler(CallbackQueryHandler(select_folder, pattern="^select_"))
    application.add_handler(MessageHandler(filters.Document.ALL & filters.Document.MimeType("application/pdf"), handle_file))

    # Run the bot until the user presses Ctrl+C or the bot is stopped
    application.run_polling()

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
