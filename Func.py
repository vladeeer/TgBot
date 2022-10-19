import random
from datetime import datetime

import Sheets

def lookFor(a,b):
	return (lambda a, b : any(i in b for i in a))(a, b)

def message_responses(input_text, user_name, credentials = None, userId = 0):
	user_message = str(input_text).lower()
	resp = ['','']

	if(lookFor(['update'], user_message)):
		error = Sheets.fetchFiles(credentials)
		if not error:
			resp[0] = "Перечень файлов обновлён"
		else:
			resp[0] = "Не удалось обновить перечень файлов"
			resp[1] = error

	elif(lookFor(['select'], user_message)):
		inp = user_message.split()
		result = [{'sheet':'', 'row':0, 'id':0}, '', '']
		if len(inp) != 2:
			resp[0] = f"Не удалось выделить строку. Допущена ошибка в команде"
			resp[1] = f'Failed to get a line by id. Invalid syntax'
		else:
			result = Sheets.getLineById(credentials, inp[1], userId)
			if not result[2]:
				resp[0] = f"Выделена строка {inp[1]} ({result[1]})"
			else:
				resp[0] = f"Не удалось выделить строку. {result[1]}"
				resp[1] = f'Failed to get a line by id. {result[2]}'

	elif(lookFor(['add'], user_message)):
		inp = user_message.split()
		if (len(inp) != 2) or (not (inp[1].isdigit())) or (not(int(inp[1]) <= 8 and int(inp[1]) >= 1)):
			resp[0] = f"Не удалось добавить строку. Допущена ошибка в команде"
			resp[1] = f'Failed to add a line. Invalid syntax'
		else:
			res = Sheets.addRow(credentials, int(inp[1]))
			if not res[1]:
				resp[0] = f'Создана строка {res[0]}'
				resp2 = message_responses(f"select {res[0]}", user_name, credentials, userId)
				resp[0] = f'{resp[0]}. {resp2[0]}'
				resp[1] = f'{resp[1]}{resp2[1]}'
			else:
				resp[0] = f"Не удалось добавить строку"
				resp[1] = f'Failed to add line. {res[1]}'

	if (not resp[0]) and (not resp[1]):
		resp[0] = "Команда не распознана, используйте /help для списка допустимых команд"

	return resp

