import random
from datetime import datetime


import Sheets

def lookFor(a,b):
	return (lambda a, b : any(i in b for i in a))(a, b)

def message_responses(input_text, user_name):
	user_message = str(input_text).lower()
	resp = ['','']
	print(str(user_name) + ": " + str(input_text))

	if(lookFor(['update'], user_message)):
		error = Sheets.fetchFiles()
		if not error:
			resp[0] = "Перечень файлов обновлён"
		else:
			resp[0] = "Не удалось обновить перечень файлов"
			resp[1] = error


	if (len(resp)==0):
		resp = "Команда не распознана, используйте /help для списка допустимых команд"

	return resp

