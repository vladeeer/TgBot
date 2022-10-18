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
										  fields='files(id, name)').execute()
		folder = response.get('files')[0]
		folder_id = folder.get('id')
		folder_name = folder.get('name')
		print(f'Found Folder: {folder_name}, {folder_id}')
		if len(response) == 0:
			print("No Folder Found") #TODO Log it

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
				print(f' - {file.get("name")}, {file.get("id")}, {str(int(int(file.get("size"))/1024))}kb, {file.get("modifiedTime")[0:10]}, {file.get("webViewLink")}')
				fileData.append([file.get("name"), int(int(file.get("size"))/1024), file.get("modifiedTime")[0:10], file.get("id"), file.get("webViewLink")])
			page_token = response.get('nextPageToken', None)
			if page_token is None:
				break

		# Get The Files Sheet
		result = sheet.get(spreadsheetId=C.FILES_ID,
						   fields='sheets(properties(title,sheetId,gridProperties(rowCount)))').execute()
		properties = result.get('sheets')[0].get('properties')
		nRows = properties.get("gridProperties").get("rowCount")
		print(f'Loaded {properties.get("title")}[{nRows}]: {properties.get("sheetId")}')
		SHEET_RANGE = properties.get('title')

		# Clear Table
		sheet.values().clear(spreadsheetId=C.FILES_ID,
							 range = f'{SHEET_RANGE}!2:{nRows}').execute()

		# Add Values
		sheet.values().append(spreadsheetId=C.FILES_ID, range=f'{SHEET_RANGE}!A1:E1', 
							  valueInputOption='USER_ENTERED', insertDataOption='OVERWRITE', 
							  body={'values': fileData}).execute()

		# TODO Get Values
		#result = sheet.values().get(spreadsheetId=C.FILES_ID,
		#							range=SHEET_RANGE+f'2:{nRows}',
		#							fields='values').execute()
		#print(result.get('values'))

	except HttpError as err:
		return str(err)

def getLineById(credentials, id):
	try:
		# Get Drive Service
		driveSrvc = build('drive', 'v3', credentials=credentials)
				
		# Get Sheets Service
		sheetsSrvc = build('sheets', 'v4', credentials=credentials)
		sheet = sheetsSrvc.spreadsheets()

		# Get Folder
		response = driveSrvc.files().list(q="mimeType='application/vnd.google-apps.folder'", 
										  spaces='drive',
										  fields='files(id, name)').execute()
		folder = response.get('files')[0]
		folder_id = folder.get('id')
		folder_name = folder.get('name')
		print(f'Found Folder: {folder_name}, {folder_id}')
		if len(response) == 0:
			print("No Folder Found") #TODO Log it

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
				print(f' - {file.get("name")}, {file.get("id")}, {str(int(int(file.get("size"))/1024))}kb, {file.get("modifiedTime")[0:10]}, {file.get("webViewLink")}')
				fileData.append([file.get("name"), int(int(file.get("size"))/1024), file.get("modifiedTime")[0:10], file.get("id"), file.get("webViewLink")])
			page_token = response.get('nextPageToken', None)
			if page_token is None:
				break

		# Get The Files Sheet
		result = sheet.get(spreadsheetId=C.FILES_ID,
						   fields='sheets(properties(title,sheetId,gridProperties(rowCount)))').execute()
		properties = result.get('sheets')[0].get('properties')
		nRows = properties.get("gridProperties").get("rowCount")
		print(f'Loaded {properties.get("title")}[{nRows}]: {properties.get("sheetId")}')
		SHEET_RANGE = properties.get('title')

		# Clear Table
		sheet.values().clear(spreadsheetId=C.FILES_ID,
							 range = f'{SHEET_RANGE}!2:{nRows}').execute()

		# Add Values
		sheet.values().append(spreadsheetId=C.FILES_ID, range=f'{SHEET_RANGE}!A1:E1', 
							  valueInputOption='USER_ENTERED', insertDataOption='OVERWRITE', 
							  body={'values': fileData}).execute()

		# TODO Get Values
		#result = sheet.values().get(spreadsheetId=C.FILES_ID,
		#							range=SHEET_RANGE+f'2:{nRows}',
		#							fields='values').execute()
		#print(result.get('values'))

	except HttpError as err:
		return str(err)



