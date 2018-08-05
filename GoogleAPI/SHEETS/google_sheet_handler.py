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


class GoogleSheetHandler():
    # Google Color Codes are available at https://material.io/guidelines/style/color.html#color-color-palette
    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/sheets.googleapis.com-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/drive'  #'https://www.googleapis.com/auth/spreadsheets'
    CLIENT_SECRET_FILE = 'datasets/client_secret.json'
    APPLICATION_NAME = 'Google Sheets API Python Quickstart'

    def __init__(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        self.service = discovery.build(
            'sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

    def get_credentials(self):
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
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE,
                                                  self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def create_google_sheet(self):
        spreadsheet_body = {}

        request = self.service.spreadsheets().create(body=spreadsheet_body)
        response = request.execute()

        print(response)
        return response

    def add_sheet(self,
                  spreadsheetId='1AXHJmdhb4L_T5ma7AR9LfGCc628qC12wygf66Or4VIw',
                  sheetIndex=0,
                  sheetName=None):
        requests = []
        request = {
            "addSheet": {
                "properties": {
                    "sheetId": sheetIndex + 1,
                    "title": sheetName
                    if sheetName else "Sheet{}".format(sheetIndex + 1),
                    "index": sheetIndex,
                    #                     "gridProperties": {
                    #                         object(GridProperties)
                    #                     },
                    "hidden": False,
                    "rightToLeft": False,
                }
            }
        }
        requests.append(request)

        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body=body).execute()
        print(response)

    def update_data_in_sheet(
            self,
            spreadsheet_id='1AXHJmdhb4L_T5ma7AR9LfGCc628qC12wygf66Or4VIw',
            range_='Sheet1!A1:D5',
            major_dimesion="ROWS",
            data_list=[["Item", "Cost", "Stocked", "Ship Date"],
                       ["Wheel", "$20.50", "4", "3/1/2016"],
                       ["Door", "$15", "2", "3/15/2016"],
                       ["Engine", "$100", "1", "3/20/2016"],
                       ["Totals", "=SUM(B2:B4)", "=SUM(C2:C4)", "=MAX(D2:D4)"]
                       ]):
        value_range_body = {
            "range": range_,
            "majorDimension": major_dimesion,
            "values": data_list
        }

        request = self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption='USER_ENTERED',
            body=value_range_body)
        response = request.execute()

        print(response)

    def update_cell(
            self,
            spreadsheetId='1AXHJmdhb4L_T5ma7AR9LfGCc628qC12wygf66Or4VIw',
            sheetIndex=0,
            rowIndex=0,
            columIndex=0,
            data_string='=SUM(C2:C4)+10',
            delimiter='\n'):
        requests = []
        request = {
            "pasteData": {
                "coordinate": {
                    "sheetId": sheetIndex + 1 if sheetIndex else sheetIndex,
                    "rowIndex": rowIndex,
                    "columnIndex": columIndex,
                },
                "data": data_string,  #"Full enjoyment no work",
                "type": "PASTE_NORMAL",
                # Union field kind can be only one of the following:
                "delimiter": delimiter,
                #"html": False,
                # End of list of possible types for union field kind.
            }
        }
        requests.append(request)

        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body=body).execute()
        print(response)

    def create_border(
            self,
            spreadsheetId='1AXHJmdhb4L_T5ma7AR9LfGCc628qC12wygf66Or4VIw',
            sheetIndex=0,
            start_row_index=0,
            end_row_index=10,
            start_col_index=0,
            end_col_index=6,
            border_width=1,
            border_style="SOLID",
            color='alpha',
            color_index=1.0):
        requests = []
        request = {
            "updateBorders": {
                "range": {
                    "sheetId": sheetIndex + 1 if sheetIndex else sheetIndex,
                    "startRowIndex": start_row_index,
                    "endRowIndex": end_row_index,
                    "startColumnIndex": start_col_index,
                    "endColumnIndex": end_col_index
                },
                "top": {
                    "style": border_style,
                    "width": border_width,
                    "color": {
                        color: color_index
                    },
                },
                "bottom": {
                    "style": border_style,
                    "width": border_width,
                    "color": {
                        color: color_index
                    },
                },
                "left": {
                    "style": border_style,
                    "width": border_width,
                    "color": {
                        color: color_index
                    },
                },
                "right": {
                    "style": border_style,
                    "width": border_width,
                    "color": {
                        color: color_index
                    },
                },
                "innerHorizontal": {
                    "style": border_style,
                    "width": border_width,
                    "color": {
                        color: color_index
                    },
                },
                "innerVertical": {
                    "style": border_style,
                    "width": border_width,
                    "color": {
                        color: color_index
                    },
                },
            }
        }
        requests.append(request)

        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body=body).execute()
        print(response)

    def merge_cells(
            self,
            spreadsheetId='1AXHJmdhb4L_T5ma7AR9LfGCc628qC12wygf66Or4VIw',
            sheetIndex=0,
            start_row_index=0,
            end_row_index=10,
            start_col_index=0,
            end_col_index=6,
            merge_type="MERGE_COLUMNS"):
        requests = []
        request = {
            "mergeCells": {
                "range": {
                    "sheetId": sheetIndex + 1 if sheetIndex else sheetIndex,
                    "startRowIndex": start_row_index,
                    "endRowIndex": end_row_index,
                    "startColumnIndex": start_col_index,
                    "endColumnIndex": end_col_index
                },
                "mergeType": merge_type
            }
        }
        requests.append(request)

        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body=body).execute()
        print(response)

    def mark_headers(
            self,
            spreadsheetId='1AXHJmdhb4L_T5ma7AR9LfGCc628qC12wygf66Or4VIw',
            sheetIndex=0,
            start_row_index=0,
            end_row_index=1,
            start_col_index=0,
            end_col_index=6,
            red_bg_color=192,
            green_bg_color=192,
            blue_bg_color=192,
            base_color=255.0,
            red_fg_color=0.0,
            green_fg_color=0.0,
            blue_fg_color=0.0,
            bold=True):
        requests = []
        request = {
            "repeatCell": {
                "range": {
                    "sheetId": sheetIndex + 1 if sheetIndex else sheetIndex,
                    "startRowIndex": start_row_index,
                    "endRowIndex": end_row_index,
                    "startColumnIndex": start_col_index,
                    "endColumnIndex": end_col_index
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": red_bg_color / base_color,
                            "green": green_bg_color / base_color,
                            "blue": blue_bg_color / base_color
                        },
                        "horizontalAlignment": "CENTER",
                        "textFormat": {
                            "foregroundColor": {
                                "red": red_fg_color / base_color,
                                "green": green_fg_color / base_color,
                                "blue": blue_fg_color / base_color
                            },
                            "fontSize": 10,
                            "bold": bold
                        }
                    }
                },
                "fields":
                "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        }
        requests.append(request)

        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body=body).execute()
        print(response)

    def read_data_from_sheet(
            self,
            spreadsheetId='1bWiB4nVUz305kUkAV1DZrxncJWz9Ccil0Dswfvu4rNk',
            rangeName='Rohit!A1:F'):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId, range=rangeName).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            for row in values[:20]:
                # Print columns A to F, which correspond to indices 0 to 5.
                print(row)
        return values

    def duplicate_sheet(self,
                        spreadsheetId=None,
                        sourceSheetId=0,
                        sheetIndex=1,
                        newSheetId=None,
                        newSheetName=''):
        requests = []
        request = {
            "duplicateSheet": {
                "sourceSheetId": sourceSheetId,
                "insertSheetIndex": sheetIndex,
                "newSheetId": newSheetId,
                "newSheetName": newSheetName
            }
        }
        requests.append(request)

        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body=body).execute()
        print(response)

    def add_column_chart(self,
                         spreadsheetId,
                         chartId=None,
                         sheetId=0,
                         usersCount=2):
        requests = []
        request = {
            "addChart": {
                "chart": {
                    "chartId": chartId,
                    "spec": {
                        # Union field chart can be only one of the following:
                        "basicChart": {
                            "chartType": "COLUMN",  # A column Chart
                            "legendPosition": "RIGHT_LEGEND",
                            "axis": [{
                                "position": "BOTTOM_AXIS"
                            }],
                            "series": [{
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": sheetId,
                                            "startRowIndex": 0,
                                            "endRowIndex": 6,
                                            "startColumnIndex": i,
                                            "endColumnIndex": i + 1
                                        }]
                                    }
                                },
                                "type": "COLUMN"
                            } for i in range(usersCount + 1)],
                            "headerCount": 1,
                            "threeDimensional": False,
                            "interpolateNulls": False,
                            "stackedType": "NOT_STACKED",
                            "lineSmoothing": False,
                            "compareMode":
                            "BASIC_CHART_COMPARE_MODE_UNSPECIFIED"
                        },
                        # End of list of possible types for union field chart.
                    },
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {
                                "sheetId": sheetId,
                                "rowIndex": 9,
                                "columnIndex": 1
                            }
                        }
                    }
                }
            }
        }
        requests.append(request)
        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body=body).execute()
        print(response)

    def add_bar_chart(self,
                      spreadsheetId,
                      chartId=None,
                      sheetId=0,
                      usersCount=2):
        requests = []
        request = {
            "addChart": {
                "chart": {
                    "chartId": chartId,
                    "spec": {
                        # Union field chart can be only one of the following:
                        "basicChart": {
                            "chartType": "BAR",  # A bar Chart
                            "legendPosition": "RIGHT_LEGEND",
                            "domains": [{
                                "domain": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": sheetId,
                                            "startRowIndex": 0,
                                            "endRowIndex": 9,
                                            "startColumnIndex": 0,
                                            "endColumnIndex": 1
                                        }]
                                    }
                                },
                                "reversed": False
                            }],
                            "series": [{
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": sheetId,
                                            "startRowIndex": 0,
                                            "endRowIndex": 9,
                                            "startColumnIndex": i,
                                            "endColumnIndex": i + 1
                                        }]
                                    }
                                }
                            } for i in range(1, usersCount + 1)],
                            "headerCount": 1,
                            "threeDimensional": False,
                            "interpolateNulls": False,
                            "stackedType": "STACKED",
                            "lineSmoothing": False,
                            "compareMode":
                            "BASIC_CHART_COMPARE_MODE_UNSPECIFIED"
                        },
                        # End of list of possible types for union field chart.
                    },
                    "position": {
                        "overlayPosition": {
                            "anchorCell": {
                                "sheetId": sheetId,
                                "rowIndex": 11,
                                "columnIndex": 1
                            }
                        }
                    }
                }
            }
        }
        requests.append(request)
        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body=body).execute()
        print(response)

    def setDataValidation(self, spreadsheetId=None, sheetId=0,
                          endRowIndex=129):
        requests = []
        request = {
            "setDataValidation": {
                "range": {
                    "sheetId": sheetId,
                    "startRowIndex": 5,
                    "endRowIndex": endRowIndex,
                    "startColumnIndex": 2,
                    "endColumnIndex": 3
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_RANGE",
                        "values": [{
                            "userEnteredValue": "=Projects!A1:A5"
                        }]
                    },
                    "inputMessage": "Choose one from Drop-down",
                    "strict": True,
                    'showCustomUi': True
                }
            }
        }
        requests.append(request)
        body = {'requests': requests}
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheetId, body=body).execute()
        print(response)


if __name__ == '__main__':
    gsh = GoogleSheetHandler()
