import os.path

from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from google.oauth2 import service_account

import Const as C
import Func as F

# Set Up And Get Credentials For APIs
SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.metadata']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')

googleCredentials = service_account.Credentials.from_service_account_file(
				SERVICE_ACCOUNT_FILE, scopes=SCOPES)

def log_message(name, text, logToTg = True):
	if (logToTg): 
		for log_chat in C.LOG_CHATS:
			dp.bot.send_message(chat_id=log_chat, text=(name + ": " + text + "\n"))
	print(name + ": " + text)
	

def start_command(update, context):
	log_message(update.message.from_user.first_name + " " + ("" if update.message.from_user.last_name is None else str(update.message.from_user.last_name)) + " [" + str(update.message.from_user.id) + "]", "Joined chat")
	log_message("Bot", "Добро пожаловать!", False)
	update.message.reply_text("Добро пожаловать!")

def help_command(update, context):
	log_message(update.message.from_user.first_name, "/help")
	log_message("Bot", "TODO Инструкция", False)
	update.message.reply_text("TODO Инструкция")

def handle_message(update, context):
	if (update.message != None and update.message.from_user.id in C.VALID_IDS):
		text=str(update.message.text)
		log_message(update.message.from_user.first_name, update.message.text, False)

		resp = F.message_responses(text, update.message.from_user.first_name, googleCredentials, update.message.from_user.id)
		if resp[0]:
			if len(resp[0]) > 100:
				log_message("Bot", f'{resp[0][0:100]}...', False)
			else:
				log_message("Bot", resp[0], False)
			update.message.reply_text(resp[0])
		if resp[1]:
			log_message("[Server]", resp[1])	
		
	
	elif (update.edited_message != None):
		log_message("Bot", "Редактирование сообщений не изменяет внесённых данных", False)
		update.edited_message.reply_text("Редактирование сообщений не изменяет внесённых данных")

def error(update, context):
	error_text = f"Update {update} causes error {context.error}"
	log_message("[Server]", error_text)

def main():
	# Set Up Tg Bot
	print("Bot strarting...")

	updater = Updater(C.TG_KEY, use_context=True)
	
	global dp 
	dp = updater.dispatcher

	dp.add_handler(CommandHandler("start", start_command))
	dp.add_handler(CommandHandler("help", help_command))

	dp.add_handler(MessageHandler(Filters.text, handle_message))

	dp.add_error_handler(error)

	log_message("Bot", "Bot started")   

	# Start Bot
	updater.start_polling()
	updater.idle()

if __name__ == "__main__":
	main()