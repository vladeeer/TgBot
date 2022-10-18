import random
from datetime import datetime

import Sheets

def lookFor(a,b):
	return (lambda a, b : any(i in b for i in a))(a, b)

def message_responses(input_text, user_name, credentials = None, userId = 0):
	user_message = str(input_text).lower()
	resp = ['','']
	print(str(user_name) + ": " + str(input_text))

	if(lookFor(['update'], user_message)):
		error = Sheets.fetchFiles(credentials)
		if not error:
			resp[0] = "Перечень файлов обновлён"
		else:
			resp[0] = "Не удалось обновить перечень файлов"
			resp[1] = error

	elif(lookFor(['select'], user_message)):
		inp = user_message.split(' ')
		result = Sheets.getLineById(credentials, inp[1], userId)
		if not result[2]:
			resp[0] = f"Выделена строка {inp[1]} ({result[1]})"
		else:
			resp[0] = f"Не удалось выделить строку. {result[1]}"
			resp[1] = f'Failed to get a line by id.\n{result[2]}'


	if (not resp[0]) and (not resp[1]):
		resp[0] = "Команда не распознана, используйте /help для списка допустимых команд"

	return resp

