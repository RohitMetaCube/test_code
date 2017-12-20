from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'  #'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'datasets/client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(
        credential_dir, 'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def update_data_in_sheet():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build(
        'sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

    # The ID of the spreadsheet to update.
    spreadsheet_id = '1AXHJmdhb4L_T5ma7AR9LfGCc628qC12wygf66Or4VIw'  # TODO: Update placeholder value.

    # The A1 notation of the values to update.
    range_ = 'Sheet1!A1:D5'  # TODO: Update placeholder value.

    value_range_body = {
        # TODO: Add desired entries to the request body. All existing entries
        # will be replaced.
        "range": "Sheet1!A1:D5",
        "majorDimension": "ROWS",
        "values": [["Item", "Cost", "Stocked", "Ship Date"],
                   ["Wheel", "$20.50", "4", "3/1/2016"],
                   ["Door", "$15", "2", "3/15/2016"],
                   ["Engine", "$100", "1", "3/20/2016"],
                   ["Totals", "=SUM(B2:B4)", "=SUM(C2:C4)", "=MAX(D2:D4)"]],
    }

    request = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_,
        valueInputOption='USER_ENTERED',
        body=value_range_body)
    response = request.execute()

    # TODO: Change code below to process the `response` dict:
    print(response)


def update_cell():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build(
        'sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '1AXHJmdhb4L_T5ma7AR9LfGCc628qC12wygf66Or4VIw'

    requests = []

    request = {
        "pasteData": {
            "coordinate": {
                "sheetId": 0,
                "rowIndex": 6,
                "columnIndex": 0,
            },
            "data": '=SUM(C2:C4)+10',  #"Full enjoyment no work",
            "type": "PASTE_NORMAL",
            # Union field kind can be only one of the following:
            "delimiter": "\n",
            #"html": False,
            # End of list of possible types for union field kind.
        }
    }

    requests.append(request)

    body = {'requests': requests}
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheetId, body=body).execute()
    print(response)


def read_data_from_sheet():
    """Shows basic usage of the Sheets API.

    Creates a Sheets API service object and prints the names and majors of
    students in a sample spreadsheet:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build(
        'sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '1bWiB4nVUz305kUkAV1DZrxncJWz9Ccil0Dswfvu4rNk'
    rangeName = 'Rohit!A1:F'
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheetId,
                                                 range=rangeName).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        for row in values[:20]:
            # Print columns A to F, which correspond to indices 0 to 5.
            print(row)


if __name__ == '__main__':
    update_data_in_sheet()
    read_data_from_sheet()
    update_cell()
