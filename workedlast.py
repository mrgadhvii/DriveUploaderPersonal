import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "7508399265:AAHZcTfGFafKEhKNjeCISDfVqEyZ4jPHPsk"
SERVICE_ACCOUNT_FILE = r"C:\Users\User\Desktop\StudyMaterial\api\service-account.json"
OWNER_ID = 7029363479  # Replace with actual owner ID
OWNER_USERNAME = "@MrGadhvii"

# Google Drive API setup
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
drive_service = build("drive", "v3", credentials=credentials)

# Folder IDs for options
FOLDER_OPTIONS = {
    "Option-1": "1jWUbr_v4T_BlcTFuGDxzJqKfacxRN9Re",
    "Option-2": "197NBp9QTxr9flCHBOKg0D3oXdvLo9dh0",
    "Option-3": "1eYTDkkfnaPIkojyQALPUQBQfob9UNl0t",
    "Option-4": "1Di_c6QYmfSI_uBvv0JQmxueEl9dEe84Z",
    "Option-5": "10ipfp_W-_ld6qlebu7lqMs2vDOikA-M-"
}

# Dictionary to track pending approvals
pending_approvals = {}

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    greeting = f"Hello, {user.first_name}! Welcome to the file upload bot. This bot is managed by {OWNER_USERNAME}. To start, use the /help command for assistance."
    await update.message.reply_text(greeting)

# /help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Welcome to the File Upload Bot! Here are the commands you can use:\n"
        "/start - Start the bot and get a greeting.\n"
        "/help - Get help with all available commands.\n"
        "/upload - Show folder options for file uploads.\n"
        "/op1, /op2, /op3, /op4, /op5 - Select a folder to upload files.\n"
        "Use /upload to see the available folder options before uploading files."
    )
    await update.message.reply_text(help_text)

# /upload command handler with inline buttons
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton(f"Option {key[-1]}", callback_data=f"select_{key}")] for key in FOLDER_OPTIONS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a folder to upload your files:", reply_markup=reply_markup)

# Callback handler for folder selection
async def select_folder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        logger.error("Received a non-callback query event.")
        return

    await query.answer()  # Confirm the callback query

    # Extract the selected option
    folder_option = query.data.split("_")[1]
    if folder_option in FOLDER_OPTIONS:
        context.user_data["selected_folder_id"] = FOLDER_OPTIONS[folder_option]
        await query.edit_message_text(f"You have selected {folder_option} for file uploads.")

        # Notify the admin for approval
        admin_message = (
            f"User {update.effective_user.first_name} ({update.effective_user.id}) has selected {folder_option} for uploading a file.\n"
            "Please respond with /yes to approve or /no to reject the upload."
        )
        pending_approvals[update.effective_user.id] = folder_option
        await context.bot.send_message(chat_id=OWNER_ID, text=admin_message)
    else:
        await query.edit_message_text("Invalid selection. Please use /upload to choose a folder.")

# Admin command handlers for approval
async def approve_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id == OWNER_ID:
        if pending_approvals:
            user_id = list(pending_approvals.keys())[0]
            folder_option = pending_approvals.pop(user_id)
            await update.message.reply_text(f"Upload approved for user {user_id} to folder {folder_option}.")
            # Proceed to upload if user has a file to send (this part would be part of the file handler)
        else:
            await update.message.reply_text("No pending uploads.")

async def reject_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id == OWNER_ID:
        if pending_approvals:
            user_id = list(pending_approvals.keys())[0]
            folder_option = pending_approvals.pop(user_id)
            await update.message.reply_text(f"Upload rejected for user {user_id}.")
            # Inform the user that the upload was rejected
            await context.bot.send_message(chat_id=user_id, text="Your file upload request was rejected.")
        else:
            await update.message.reply_text("No pending uploads.")

# File handler for users
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.document.mime_type == "application/pdf":
        selected_folder_id = context.user_data.get("selected_folder_id")
        if selected_folder_id:
            # Check if there is pending approval for this user
            if update.effective_user.id in pending_approvals:
                await update.message.reply_text("Your file is awaiting admin approval. Please wait for a response.")
            else:
                # Process file upload
                file = await update.message.document.get_file()
                file_path = f"./{update.message.document.file_name}"
                await file.download_to_drive(file_path)

                # Upload to the selected folder
                file_metadata = {"name": os.path.basename(file_path), "parents": [selected_folder_id]}
                media = MediaFileUpload(file_path, mimetype="application/pdf")
                drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

                # Clean up local file storage
                os.remove(file_path)

                await update.message.reply_text("File uploaded successfully to the selected folder.")
        else:
            await update.message.reply_text("You need to select a folder first using /upload.")
    else:
        await update.message.reply_text("Only PDF files are allowed!")

# Main function
def main() -> None:
    # Create the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("upload", upload))
    application.add_handler(CallbackQueryHandler(select_folder, pattern="^select_"))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_file))
    application.add_handler(CommandHandler("yes", approve_upload))
    application.add_handler(CommandHandler("no", reject_upload))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
