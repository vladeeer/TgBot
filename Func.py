from datetime import datetime

import Sheets

def lookFor(a,b):
	return (lambda a, b : any(i in b.lower() for i in a))(a, b)

def message_responses(input_text, user_name, credentials = None, userId = 0):
	user_message = str(input_text)
	resp = ['','']

	if(lookFor(['update'], user_message)):
		error = Sheets.fetchFiles(credentials)
		if not error:
			resp[0] = "Перечень файлов обновлён"
		else:
			resp[0] = f'Не удалось обновить перечень файлов{error[0]}'
			resp[1] = f'Failed to update Files table. {error[1]}'

	elif(lookFor(['select'], user_message)):
		inp = user_message.split()
		if len(inp) != 2:
			resp[0] = f'Не удалось выделить строку. Допущена ошибка в команде'
		else:
			res = Sheets.getLineById(credentials, inp[1], userId)
			if not res[2]: 
				resp[0] = f'Выделена строка id:{inp[1]} ({res[1]})'
			else:
				resp[0] = f'Не удалось выделить строку{res[1]}'
				if res[2]:
					resp[1] = f'Failed to get a line by id. {res[2]}'

	elif(lookFor(['add'], user_message)):
		inp = user_message.split()
		if (len(inp) != 2) or (not (inp[1].isdigit())) or (not(int(inp[1]) <= 8 and int(inp[1]) >= 1)):
			resp[0] = f'Не удалось добавить строку. Допущена ошибка в команде'
		else:
			res = Sheets.addRow(credentials, int(inp[1]))
			if not res[1] and not res[2]:
				resp[0] = f'Создана строка id:{res[0]}'
				resp2 = message_responses(f'select {res[0]}', user_name, credentials, userId)
				resp[0] = f'{resp[0]}. {resp2[0]}'
				resp[1] = f'{resp[1]}{resp2[1]}'
			else:
				resp[0] = f'Не удалось добавить строку{res[1]}'
				if res[2]:
					resp[1] = f'Failed to add line. {res[2]}'

	elif(lookFor(['id'], user_message)):
		res = Sheets.getUserData(credentials, userId)
		if not res[1] and not res[2]:
			resp[0] = f'Выделена строка id:{res[0][5]} ({res[0][3]}!{res[0][4]})'
		else:
			resp[0] = f'Не удалось определить выделенную строку{res[1]}'
			if res[2]:
				resp[1] = f'Failed to get id of selected. {res[2]}'

	elif(lookFor(['get'], user_message)):
		res = Sheets.getRow(credentials, userId)
		if not res[1] and not res[2]:
			resp[0] = (f"Отм: {res[0][0]}\n"
					   f"Дата: {res[0][1]}\n"
					   f"Имя файла: {res[0][2]}\n"
					   f"Контрагент: {res[0][3]}\n"
					   f"Сумма: {res[0][4]}\n"
					   f"Плательщик: {res[0][6]} {res[0][5]}\n"
					   f"Налогооблажение: {res[0][8]} {res[0][7]}\n"
					   f"Назначение: {res[0][9]}\n"
					   f"№ счёта: {res[0][10]}\n"
					   f"Дата документа: {res[0][11]}\n"
					   f"Объект списания: {res[0][13]} {res[0][12]}\n"
					   f"Статья расходов: {res[0][15]} {res[0][14]}\n"
					   f"Дата реестра: {res[0][16]}\n"
					   f"Ответственный: {res[0][17]}\n"
					   f"Id: {res[0][18]}\n"
					   f"Ссылка: {res[0][19]}\n")
		else:
			resp[0] = f'Не удалось получить выделенную строку{res[1]}'
			if res[2]:
				resp[1] = f'Failed to get selected line. res[2]'

	elif(lookFor(['free'], user_message)):
		res = Sheets.getFreeId(credentials)
		if not res[1] and not res[2]:
			resp[0] = f'Свободный id:{res[0]}'
		else:
			resp[0] = f'Не удалось найти свободный id{res[1]}'
			if res[2]:
				resp[1] = f'Failed to get free id. {res[2]}'

	elif(lookFor(['file'], user_message)):
		msg = user_message.split()
		if (len(msg) < 2):
			resp[0] = f'Не удалось добавить файл. Допущена ошибка в команде'
		else:
			inp = [msg[0], msg[1]]
			if len(msg) > 2:
				for word in msg[2:]:
					inp[1] = inp[1] + ' ' + word

			res = Sheets.addFile(credentials, userId, inp[1])
			if not res[1] and not res[2]:
				resp[0] = f'Добавлен файл {inp[1]}'
			else:
				resp[0] = f'Не удалось добавить файл{res[1]}'
				if res[2]:
					resp[1] = f'Failed to add line. {res[2]}'

	elif(lookFor(['next'], user_message)):
		res = Sheets.nextRow(credentials, userId)
		if not res[1] and not res[2]:
			resp[0] = f"Выделена строка id:{res[0].get('id')} ({res[0].get('sheet')}!{res[0].get('row')})"
		else:
			resp[0] = f'Не удалось выделить следующую строку{res[1]}'
			if res[2]:
				resp[1] = f'Failed to select next row. {res[2]}'

	elif(lookFor(['prev'], user_message)):
		res = Sheets.prevRow(credentials, userId)
		if not res[1] and not res[2]:
			resp[0] = f"Выделена строка id:{res[0].get('id')} ({res[0].get('sheet')}!{res[0].get('row')})"
		else:
			resp[0] = f'Не удалось выделить предшевствующую строку{res[1]}'
			if res[2]:
				resp[1] = f'Failed to select previous row. {res[2]}'
	
	elif(user_message.lower() == 'f'):
		resp[0] = """Шпаргалка по номерам (#) полей:
			User1: 1-Описание, 2-Ответственный(№), 
		3-Объект(№), 4-Статья расходов(№), 
		5-Сумма
			User2: 1-Плательщик(№), 2-Налоги(№), 
		3-Дата реестра
			User3: 1-№ счёта, 2-Дата документа, 
		3-Контрагент(№)"""

	elif(lookFor(['f1', 'f2', 'f3', 'f4', 'f5'], user_message)):
		msg = user_message.split()
		if (len(msg) < 2):
			resp[0] = f'Не удалось добавить файл. Допущена ошибка в команде'
		else:
			inp = [msg[0], msg[1]]
			if len(msg) > 2:
				for word in msg[2:]:
					inp[1] = inp[1] + ' ' + word

			res = Sheets.addFile(credentials, userId, inp[1])
			if not res[1] and not res[2]:
				resp[0] = f'Добавлен файл {inp[1]}'
			else:
				resp[0] = f'Не удалось добавить файл{res[1]}'
				if res[2]:
					resp[1] = f'Failed to add line. {res[2]}'

	if (not resp[0]) and (not resp[1]):
		resp[0] = 'Команда не распознана, используйте /help для списка допустимых команд'

	return resp

