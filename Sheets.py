from fileinput import filename
from wsgiref import validate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import Const as C

def fetchFiles(credentials):
	try:
		# Get Drive Service
		driveSrvc = build('drive', 'v3', credentials=credentials)
				
		# Get Sheets Service
		sheetsSrvc = build('sheets', 'v4', credentials=credentials)
		sheet = sheetsSrvc.spreadsheets()

		# Get Folder
		response = driveSrvc.files().list(q="mimeType='application/vnd.google-apps.folder'", 
										  spaces='drive',
										  fields='files(id)').execute()
		if len(response.get('files')) == 0:
			return ['Не найден каталог с файлами', '']
		folder = response.get('files')[0]
		folder_id = folder.get('id')

		# Get all the files within the folder
		fileData = []
		page_token = None
		while True:
			response = driveSrvc.files().list(q=f"parents in '{folder_id}'",
											  spaces='drive',
											  fields='nextPageToken, files(id, name, size, modifiedTime, webViewLink)',
											  pageToken=page_token).execute()
			for file in response.get('files', []):
				#print(f' - {file.get("name")}, {file.get("id")}, {str(int(int(file.get("size"))/1024))}kb, {file.get("modifiedTime")[0:10]}, {file.get("webViewLink")}')
				fileData.append([file.get("name"), int(int(file.get("size"))/1024), file.get("modifiedTime")[0:10], file.get("id"), file.get("webViewLink")])
			page_token = response.get('nextPageToken', None)
			if page_token is None:
				break

		# Get The Files Sheet
		result = sheet.get(spreadsheetId=C.FILES_ID,
						   fields='sheets(properties(title,gridProperties(rowCount)))').execute()
		properties = result.get('sheets')[0].get('properties')
		nRows = properties.get('gridProperties').get('rowCount')
		sheetRange = properties.get('title')

		# Clear Table
		sheet.values().clear(spreadsheetId=C.FILES_ID,
							 range = f'{sheetRange}!2:{nRows}').execute()

		# Add Values
		sheet.values().append(spreadsheetId=C.FILES_ID, range=f'{sheetRange}!A1:E1', 
							  valueInputOption='USER_ENTERED', insertDataOption='OVERWRITE', 
							  body={'values': fileData}).execute()

		# TODO Get Values
		#result = sheet.values().get(spreadsheetId=C.FILES_ID,
		#							range=SHEET_RANGE+f'2:{nRows}',
		#							fields='values').execute()
		#print(result.get('values'))

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return ['. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return ['', str(err)]

def getLineById(credentials, id, userId = 0, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Get non-First Sheet Names
		result = sheet.get(spreadsheetId=C.REG_ID,
						   fields='sheets(properties(title,sheetId))').execute()
		names = [result.get('sheets')[i].get('properties').get('title') for i in range(1, len(result.get('sheets')))]

		# Find Sheet & Row With id
		foundRow = -1
		foundSheet = ''

		for i in range(0, len(names)):  # TODO Use BatchGet
			result = sheet.values().get(spreadsheetId=C.REG_ID, 
										range=f"'{names[i]}'!S4:S",
										valueRenderOption='FORMATTED_VALUE',
										fields='values').execute()
			if not result.get('values'):
				continue
			array = result.get('values')
			for j in range(0, len(array)):
				if not len(array[j]):
					array[j] = '0'
				else:
					array[j] = array[j][0]

			try:
				foundRow = 3 + 1 + array.index(id)
				foundSheet = names[i]
				break
			except ValueError:
				continue
		
		if foundRow == -1:
			return [{'sheet':'', 'row':0, 'id':0}, f'. Строка с номером {id} не найдена', ' ']

		# Return if no User Specified else write selection to USERS_ID
		if (userId == 0):
			return [{'sheet':foundSheet, 'row':foundRow, 'id':int(id)}, f'\'{foundSheet}\'!{foundRow}','']

		# Get User's Row
		res = getUserRow(credentials, userId, sheet)
		userRow = res[0]
		if res[1]:
			return [{'sheet':'', 'row':0, 'id':0}, '', f'{res[1]}']

		if not userRow:
			return [{'sheet':'', 'row':0, 'id':0}, '. Недостаточно прав для доступа', f'Denied access {userId}']
		
		# Update Users Sheet
		userData = [[f'\'\'{foundSheet}\'', foundRow, str(id)]]
		sheet.values().update(spreadsheetId=C.USERS_ID, range=f'D{userRow}:F{userRow}', 
							  valueInputOption='USER_ENTERED',
							  body={'values': userData}).execute()

		return [{'sheet':foundSheet, 'row':int(foundRow), 'id':int(id)}, f'\'{foundSheet}\'!{foundRow}', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return [{'sheet':'', 'row':0, 'id':0}, '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return [{'sheet':'', 'row':0, 'id':0}, '', str(err)]

def getUserRow(credentials, userId, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Find Current User's Line
		result = sheet.values().get(spreadsheetId=C.USERS_ID, 
										range='A2:A',
										fields='values').execute()
		array = [i[0] for i in result.get('values')]
		try:
			userRow = 2 + array.index(str(userId))
		except ValueError:
			return [None, '. Пользователь не найден', '']

		return [userRow, '', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return [None, '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return [None, '', str(err)]

def getUserData(credentials, userId, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Get User Row
		res = getUserRow(credentials, userId, sheet)
		userRow = res[0]
		if res[1] or res[2]:
			return [None, res[1], res[2]]

		if not userRow:
			return [None, '. Пользователь не найден', '']

		# Get User's Line
		result = sheet.values().get(spreadsheetId=C.USERS_ID, 
									range=f"A{userRow}:F{userRow}",
									fields='values').execute()
		if not result.get('values'):
			return [None, '. Пользователь не найден', '']

		return [result.get('values')[0], '', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return [None, '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return [None, '', str(err)]

def getFreeId(credentials, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Get non-First Sheet Names
		result = sheet.get(spreadsheetId=C.REG_ID,
						   fields='sheets(properties(title,sheetId))').execute()
		names = [result.get('sheets')[i].get('properties').get('title') for i in range(1, len(result.get('sheets')))]

		# Get Sorted List of Ids
		ids = []
		for i in range(0, len(names)):  # TODO Use BatchGet
				result = sheet.values().get(spreadsheetId=C.REG_ID, 
											range=f"'{names[i]}'!S4:S",
											fields='values').execute()
				if not result.get('values'):
					continue
				array = [int(i[0]) for i in result.get('values') if len(i)]
				ids.extend(array)
		
		ids.sort()

		# Get Missing/Next Id
		if len(ids) == 0:
			return [1, '', '']

		if len(ids) == 1:
			return [ids[0] + 1, '', '']

		for i in range(0, len(ids)):
			if ids[i] != i + 1:
				return [i + 1, '', '']
		return [ids[len(ids)-1] + 1, '', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return [None, '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return [None, '', str(err)]

def addRow(credentials, sheetId, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Get non-First Sheet Names
		result = sheet.get(spreadsheetId=C.REG_ID,
						   fields='sheets(properties(title,sheetId))').execute()
		names = [result.get('sheets')[i].get('properties').get('title') for i in range(1, len(result.get('sheets')))]
		sheetIds2 = [result.get('sheets')[i].get('properties').get('sheetId') for i in range(1, len(result.get('sheets')))]  
		name = names[sheetId-1]
		sheetId2 = sheetIds2[sheetId-1]

		# Get New Id
		res = getFreeId(credentials, sheet)
		lineId = str(res[0])
		if res[1] or res[2]:
			return ['', res[1], res[2]]

		# Get Next Row
		result = sheet.values().get(spreadsheetId=C.REG_ID,
									range=f"'{name}'!S4:S",
									valueRenderOption='FORMATTED_VALUE',
									fields='values').execute()

		lineRow = 0
		values =result.get('values')
		for j in range(0, len(values)):
				if not len(values[j]):
					lineRow = 4 + j
					break
		
		if lineRow == 0:
			lineRow = 4 + len(values)

		# Get Next Line
		lineData = ['']*20; lineData[18] = lineId
		sheet.values().update(spreadsheetId=C.REG_ID, range=f"'{name}'!A{lineRow}:T{lineRow}", 
							  valueInputOption='USER_ENTERED',
							  body={'values': [lineData]}).execute()

		# Copy Formating and Formualas From Row 1
		body = {'requests': [
			{
				'copyPaste': {
					'source': {
						'sheetId': sheetId2,
						'startRowIndex': 3,
						'endRowIndex': 4,
						'startColumnIndex': 0,
						'endColumnIndex': 20
					},
					'destination': {
						'sheetId': sheetId2,
						'startRowIndex': lineRow-1,
						'endRowIndex': lineRow,
						'startColumnIndex': 0,
						'endColumnIndex': 20
					},
					'pasteType': 'PASTE_FORMAT'
				}
			},
			{
				'copyPaste': {
					'source': {
						'sheetId': sheetId2,
						'startRowIndex': 3,
						'endRowIndex': 4,
						'startColumnIndex': 6,
						'endColumnIndex': 7
					},
					'destination': {
						'sheetId': sheetId2,
						'startRowIndex': lineRow-1,
						'endRowIndex': lineRow,
						'startColumnIndex': 6,
						'endColumnIndex': 7
					},
					'pasteType': 'PASTE_FORMULA'
				}
			},
			{
				'copyPaste': {
					'source': {
						'sheetId': sheetId2,
						'startRowIndex': 3,
						'endRowIndex': 4,
						'startColumnIndex': 8,
						'endColumnIndex': 9
					},
					'destination': {
						'sheetId': sheetId2,
						'startRowIndex': lineRow-1,
						'endRowIndex': lineRow,
						'startColumnIndex': 8,
						'endColumnIndex': 9
					},
					'pasteType': 'PASTE_FORMULA'
				}
			},
			{
				'copyPaste': {
					'source': {
						'sheetId': sheetId2,
						'startRowIndex': 3,
						'endRowIndex': 4,
						'startColumnIndex': 13,
						'endColumnIndex': 14
					},
					'destination': {
						'sheetId': sheetId2,
						'startRowIndex': lineRow-1,
						'endRowIndex': lineRow,
						'startColumnIndex': 13,
						'endColumnIndex': 14
					},
					'pasteType': 'PASTE_FORMULA'
				}
			},
			{
				'copyPaste': {
					'source': {
						'sheetId': sheetId2,
						'startRowIndex': 3,
						'endRowIndex': 4,
						'startColumnIndex': 15,
						'endColumnIndex': 16
					},
					'destination': {
						'sheetId': sheetId2,
						'startRowIndex': lineRow-1,
						'endRowIndex': lineRow,
						'startColumnIndex': 15,
						'endColumnIndex': 16
					},
					'pasteType': 'PASTE_FORMULA'
					}
			}]}
		result = sheet.batchUpdate(spreadsheetId=C.REG_ID, body=body).execute()

		return [f'{lineId}', '', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return ['', '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return ['', '', str(err)]
	
def getRow(credentials, userId, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Get User Row
		res = getUserData(credentials, userId, sheet)
		userRow = res[0]
		if res[1] or res[2]:
			return [None, res[1], res[2]]

		# Get User Line
		regSheet = userRow[3]
		regRow = userRow[4]

		result = sheet.values().get(spreadsheetId=C.REG_ID, 
									range=f'{regSheet}!A{regRow}:T{regRow}',
									valueRenderOption='FORMATTED_VALUE',
									fields='values').execute()
		if not result.get('values'):
			return [None, '. Строка пользователя пуста (Происходить не должно!!!)', '']

		values = result.get('values')[0]
		while len(values) < 20:
			values.append('')

		return [values, '', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return [None, '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return [None, '', str(err)]

def addFile(credentials, userId, fileName, sheet = None):
	try:
		# Get Sheets Service        ;
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Find File Row           
		result = sheet.values().get(spreadsheetId=C.FILES_ID, 
										range='A2:A',
										fields='values').execute() 
		array = [i[0] for i in result.get('values')]        
		try:
			fileRow = 2 + array.index(str(fileName))          
		except ValueError:
			return [None, '. Файл не найден', '']

		result = sheet.values().get(spreadsheetId=C.FILES_ID, 
										range=f'A{fileRow}:F{fileRow}',
										fields='values').execute()
		fileData = result.get('values')[0]					

		# Get User Row
		res = getUserData(credentials, userId, sheet)
		userRow = res[0]									
		if res[1] or res[2]:
			return [None, res[1], res[2]]

		# Get User Line
		regSheet = userRow[3]
		regRow = userRow[4]

		# Update Name & Date
		sheet.values().update(spreadsheetId=C.REG_ID, range=f'{regSheet}!B{regRow}:C{regRow}', 
							  valueInputOption='USER_ENTERED',
							  body={'values': [[fileData[2], fileData[0]]]}).execute()

		# Update Link
		sheet.values().update(spreadsheetId=C.REG_ID, range=f'{regSheet}!T{regRow}', 
							  valueInputOption='USER_ENTERED',
							  body={'values': [[fileData[4]]]}).execute()

		return [None, '', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return [None, '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return [None, '', str(err)]

def nextRow(credentials, userId, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Get User Data
		res = getUserData(credentials, userId, sheet)
		userRow = res[0]									
		if res[1] or res[2]:
			return [None, res[1], res[2]]

		# Get User Line
		regSheet = userRow[3]
		regRow = int(userRow[4])

		result = sheet.values().get(spreadsheetId=C.REG_ID, 
									range=f"{regSheet}!S4:S",
									valueRenderOption='FORMATTED_VALUE',
									fields='values').execute()
			
		newRow = regRow
		while True:
			newRow = newRow + 1
			if newRow - 3 <= len(result.get('values')):
				if result.get('values')[newRow - 4] and (result.get('values')[newRow - 4][0].isdigit()):
					break
			else:
				return [{'sheet':'', 'row':0, 'id':0}, f'. Достигнута последняя строка', '']

		newId = result.get('values')[newRow - 4][0]

		# Get User's Row
		res = getUserRow(credentials, userId, sheet)
		userRow = res[0]
		if res[1]:
			return [{'sheet':'', 'row':0, 'id':0}, '', f'{res[1]}']

		if not userRow:
			return [{'sheet':'', 'row':0, 'id':0}, '. Недостаточно прав для доступа', f'Denied access {userId}']
		
		# Update Users Sheet
		userData = [[f'\'{regSheet}', str(newRow), newId]]
		sheet.values().update(spreadsheetId=C.USERS_ID, range=f'D{userRow}:F{userRow}', 
							  valueInputOption='USER_ENTERED',
							  body={'values': userData}).execute()

		return [{'sheet':regSheet, 'row':newRow, 'id':newId}, '', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return [{'sheet':'', 'row':0, 'id':0}, '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return [{'sheet':'', 'row':0, 'id':0}, '', str(err)]

def prevRow(credentials, userId, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Get User Data
		res = getUserData(credentials, userId, sheet)
		userRow = res[0]									
		if res[1] or res[2]:
			return [None, res[1], res[2]]

		# Get User Line
		regSheet = userRow[3]
		regRow = int(userRow[4])

		result = sheet.values().get(spreadsheetId=C.REG_ID, 
									range=f"{regSheet}!S4:S",
									valueRenderOption='FORMATTED_VALUE',
									fields='values').execute()
			
		newRow = regRow
		while True:
			newRow = newRow - 1
			if newRow - 3 >= 1:
				if result.get('values')[newRow - 4] and (result.get('values')[newRow - 4][0].isdigit()):
					break
			else:
				return [{'sheet':'', 'row':0, 'id':0}, f'. Достигнута первая строка', '']

		newId = result.get('values')[newRow - 4][0]

		# Get User's Row
		res = getUserRow(credentials, userId, sheet)
		userRow = res[0]
		if res[1]:
			return [{'sheet':'', 'row':0, 'id':0}, '', f'{res[1]}']

		if not userRow:
			return [{'sheet':'', 'row':0, 'id':0}, '. Недостаточно прав для доступа', f'Denied access {userId}']
		
		# Update Users Sheet
		userData = [[f'\'{regSheet}', str(newRow), newId]]
		sheet.values().update(spreadsheetId=C.USERS_ID, range=f'D{userRow}:F{userRow}', 
							  valueInputOption='USER_ENTERED',
							  body={'values': userData}).execute()

		return [{'sheet':regSheet, 'row':newRow, 'id':newId}, '', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return [{'sheet':'', 'row':0, 'id':0}, '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return [{'sheet':'', 'row':0, 'id':0}, '', str(err)]

def getField(credentials, userId, fieldStr, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Get User Row
		res = getUserData(credentials, userId, sheet)
		userRow = res[0]
		if res[1] or res[2]:
			return [None, res[1], res[2]]

		# Get User Line
		userPos = int(userRow[1])
		regSheet = userRow[3]
		regRow = userRow[4]

		res = getColIndex(fieldStr, userPos)
		col = res[0].get('col')
		if res[1]:
			return [None, res[1], '']

		result = sheet.values().get(spreadsheetId=C.REG_ID, 
									range=f'{regSheet}!{col}{regRow}',
									valueRenderOption='FORMATTED_VALUE',
									fields='values').execute()
		if not result.get('values'):
			return ['', '', '']

		return [result.get('values')[0][0], '', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return [None, '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return [None, '', str(err)]

def setField(credentials, userId, fieldStr, fieldValue, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Get User Row
		res = getUserData(credentials, userId, sheet)
		userRow = res[0]
		if res[1] or res[2]:
			return [None, res[1], res[2]]

		# Get User Line
		userPos = int(userRow[1])
		regSheet = userRow[3]
		regRow = userRow[4]

		res = getColIndex(fieldStr, userPos)
		col = res[0].get('col')
		isInt = res[0].get('isInt')
		if res[1]:
			return [None, res[1], '']

		if isInt and not fieldValue.isdigit():
			return [None, '. Выбранное поле должно иметь численное значение', '']

		sheet.values().update(spreadsheetId=C.REG_ID, range=f'{regSheet}!{col}{regRow}', 
							  valueInputOption='USER_ENTERED',
							  body={'values': [[fieldValue]]}).execute()

		return [None, '', '']

	except HttpError as err:
		if err.resp.reason == 'Too Many Requests':
			return [None, '. Превышен лимит запросов, подождите 60 секунд', str(err)]
		return [None, '', str(err)]

def getColIndex(fieldStr, userPos):
	if userPos == 1 and fieldStr == 'f1':
		return [{'col':'J', 'isInt':False}, ''] # Описание
	elif userPos == 1 and fieldStr == 'f2':
		return [{'col':'R', 'isInt':False}, ''] # Ответственный
	elif userPos == 1 and fieldStr == 'f3':
		return [{'col':'M', 'isInt':True}, '']  # Объект списания
	elif userPos == 1 and fieldStr == 'f4':
		return [{'col':'O', 'isInt':True}, '']  # Статья расходов
	elif userPos == 1 and fieldStr == 'f5':
		return [{'col':'E', 'isInt':True}, '']  # Сумма
	elif userPos == 2 and fieldStr == 'f1':
		return [{'col':'F', 'isInt':True}, '']  # Плательщик
	elif userPos == 2 and fieldStr == 'f2':
		return [{'col':'H', 'isInt':True}, '']  # Налогооблажение
	elif userPos == 2 and fieldStr == 'f3':
		return [{'col':'Q', 'isInt':False}, ''] # Дата реестра
	elif userPos == 3 and fieldStr == 'f1':
		return [{'col':'K', 'isInt':True}, '']  # № счёта
	elif userPos == 3 and fieldStr == 'f2':
		return [{'col':'L', 'isInt':False}, ''] # Дата документа
	elif userPos == 3 and fieldStr == 'f3':
		return [{'col':'D', 'isInt':False}, ''] # Контрагент
	else:
		return [{'col':'', 'isInt':False}, '. Указано неверное поле']