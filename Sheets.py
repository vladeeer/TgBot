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
			return "Не найден каталог с файлами"
		folder = response.get('files')[0]
		folder_id = folder.get('id')

		# Get all the files within the folder
		fileData = []
		page_token = None
		while True:
			response = driveSrvc.files().list(q=f"parents in '{folder_id}'",
											  spaces='drive',
											  fields='nextPageToken, '
											  'files(id, name, size, modifiedTime, webViewLink)',
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
		nRows = properties.get("gridProperties").get("rowCount")
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
		return str(err)

def getLineById(credentials, id, userId = 0, sheet = None):
	try:
		# Get Sheets Service
		if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

		# Get non-First Sheet Names and Sizes
		result = sheet.get(spreadsheetId=C.REG_ID,
						   fields='sheets(properties(title,sheetId))').execute()
		names = [result.get('sheets')[i].get('properties').get('title') for i in range(1, len(result.get('sheets')))]

		# Find Sheet & Row With id
		foundRow = -1
		foundSheet = ''

		for i in range(0, len(names)):  # TODO Use BatchGet
			result = sheet.values().get(spreadsheetId=C.REG_ID, 
										range=f"'{names[i]}'!S4:S",
										fields='values').execute()
			array = [i[0] for i in result.get('values')]
			try:
				foundRow = 3 + 1 + array.index(id)
				foundSheet = names[i]
				break
			except ValueError:
				continue
		
		if foundRow == -1:
			return [{'sheet':'', 'row':0, 'id':0}, f'Строка с номером {id} не найдена', ' ']

		# Return if no User Specified else write selection to USERS_ID
		if (userId == 0):
			return [{'sheet':foundSheet, 'row':foundRow, 'id':int(id)}, f'\'{foundSheet}\':{foundRow}','']

		# Get User's Row
		userRow = getUserRow(credentials, userId, sheet)
		if not userRow:
			return [{'sheet':'', 'row':0, 'id':0}, 'Недостаточно прав для доступа', f'Попытка доступа {userId}']

		# Update Users Sheet
		userData = [[f'\'{foundSheet}\'', foundRow, str(id)]]
		sheet.values().update(spreadsheetId=C.USERS_ID, range=f'D2:F2', 
							  valueInputOption='USER_ENTERED',
							  body={'values': userData}).execute()

		return [{'sheet':foundSheet, 'row':int(foundRow), 'id':int(id)}, f'\'{foundSheet}\':{foundRow}', '']

	except HttpError as err:
		return [{'sheet':'', 'row':0, 'id':0}, '', str(err)]

def getUserRow(credentials, userId, sheet = None):
	# Get Sheets Service
	if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

	# Find Current User's Line
	userRow = -1

	result = sheet.values().get(spreadsheetId=C.USERS_ID, 
									range="A2:A",
									fields='values').execute()
	array = [i[0] for i in result.get('values')]
	try:
		userRow = 1 + 1 + array.index(str(userId))
	except ValueError:
		return None

	return userRow

def getUserData(credentials, userId, sheet = None):
	# Get Sheets Service
	if not sheet:
			sheet = build('sheets', 'v4', credentials=credentials).spreadsheets()

	# Get User Row
	userRow = getUserRow(credentials, userId, sheet)
	if not userRow:
		return None

	# Get User's Line
	result = sheet.values().get(spreadsheetId=C.USERS_ID, 
								range=f"A{userRow}:E{userRow}",
								fields='values').execute()

	return result.get('values')

	



