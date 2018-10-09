from __future__ import print_function
import httplib2
import os, sys

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import logging
import googleapiclient
import json
import time
from log_utils import OneLineExceptionFormatter

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# importing enum for enumerations 
import enum


# creating enumerations using class 
class Format(enum.Enum):
    CENTER = "CENTER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    WRAP = "WRAP"
    NO_WRAPING = "WRAP_STRATEGY_UNSPECIFIED"
    OVERFLOW_CELL = "OVERFLOW_CELL"
    LEGACY_WRAP = "LEGACY_WRAP"
    CLIP = "CLIP"


class GoogleSheetHandler():
    # Google Color Codes are available at https://material.io/guidelines/style/color.html#color-color-palette
    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/sheets.googleapis.com-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/drive'  #'https://www.googleapis.com/auth/spreadsheets'
    CLIENT_SECRET_FILE = 'datasets/client_secret.json'
    APPLICATION_NAME = 'Google Sheets API Python Quickstart'
    LOG_FORMAT_STRING = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        self.service = discovery.build(
            'sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)
        self.drive_service = discovery.build(
            'drive', 'v3', credentials=credentials)

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

    def format_logging(self):
        logging_handler = logging.StreamHandler(sys.stdout)
        log_format = OneLineExceptionFormatter(
            GoogleSheetHandler.LOG_FORMAT_STRING,
            GoogleSheetHandler.LOG_TIME_FORMAT)
        logging_handler.setFormatter(log_format)
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(logging_handler)

    def share_google_spreadsheet(self, share_emails=[], spreadsheetId=None):
        if share_emails:
            for emailAddr in share_emails:
                # https://developers.google.com/drive/v3/web/manage-sharing#roles
                # https://developers.google.com/drive/v3/reference/permissions#resource-representations
                domain_permission = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': emailAddr
                }

                req = self.drive_service.permissions().create(
                    fileId=spreadsheetId,
                    sendNotificationEmail=True,
                    emailMessage="This is an Auto Generated Mail of file sharing",
                    body=domain_permission)
                req.execute()

    def create_google_sheet(self, projectName=None, month=None, year=None):
        response = None
        spreadsheet_body = {
            "properties": {
                "title": "{} {} {} Timesheet".format(projectName, month, year)
            }
        }
        while True:
            logging.info(
                "googleSheetHandler.CreateGoogleSheet ::: Creating a new spreadsheet...."
            )
            try:
                request = self.service.spreadsheets().create(
                    body=spreadsheet_body)
                response = request.execute()
                break
            except googleapiclient.errors.HttpError as e:
                logging.info(
                    "googleSheetHandler.CreateGoogleSheet ::: {}".format(e))
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:
                    time.sleep(60)
                    continue
                else:
                    break
            except Exception as e:
                logging.info(
                    "googleSheetHandler.CreateGoogleSheet ::: {}".format(e))
                break
        logging.info(response)
        return response

    def rename_spreadsheet(self,
                           spreadsheetName=None,
                           projectName=None,
                           month=None,
                           year=None,
                           requests=[]):
        request = {
            "UpdateSpreadsheetPropertiesRequest": {
                "properties": {
                    "title": spreadsheetName if spreadsheetName else
                    "{} {} {} Timesheet".format(projectName, month, year),
                }
            }
        }
        requests.append(request)
        return requests

    def get_all_existing_sheet_indexes(self, spreadsheetId=None):
        sheet_metadata = self.service.spreadsheets().get(
            spreadsheetId=spreadsheetId).execute()
        sheets = sheet_metadata.get('sheets', '')
        id_title_map = {}
        for sheet in sheets:
            title = sheet.get("properties", {}).get("title", "Sheet1")
            sheet_id = sheet.get("properties", {}).get("sheetId", 0)
            id_title_map[sheet_id] = title
        return id_title_map

    def process_batch_requests(self, spreadsheetId=None, requests=[]):
        status = False
        response = None
        if spreadsheetId and requests:
            body = {'requests': requests}
            logging.info("{}".format(body))
            try:
                response = self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheetId, body=body).execute()
                logging.info(
                    "googleSheetHandler.ProcessingBatchRequests ::: {}".format(
                        response))
                return True, response
            except googleapiclient.errors.HttpError as e:
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:  # Access Limit Crossed
                    time.sleep(60)
                    status, response = self.process_batch_requests(
                        spreadsheetId=spreadsheetId, requests=requests)
                else:
                    logging.info(
                        "googleSheetHandler.ProcessingBatchRequests ::: {}".
                        format(e))
            except Exception as e:
                logging.info(
                    "googleSheetHandler.ProcessingBatchRequests ::: {}".format(
                        e))
        else:
            logging.info(
                "googleSheetHandler.ProcessingBatchRequests ::: Please Provide a valid spreadsheetId and requests array"
            )
        return status, response

    def add_sheet(self, sheetIndex=0, sheetName=None, requests=[]):
        request = {
            "addSheet": {
                "properties": {
                    "sheetId": sheetIndex,
                    "title": sheetName
                    if sheetName else "Sheet{}".format(sheetIndex + 1),
                    "index": sheetIndex,
                    "hidden": False,
                    "rightToLeft": False,
                }
            }
        }
        requests.append(request)
        return requests

    def update_data_in_sheet(
            self,
            spreadsheetId=None,
            range_='',  # Sample value: 'Sheet1!A1:D5',
            major_dimesion="ROWS",
            data_list=[]):
        status = False
        if spreadsheetId and range_ and data_list:
            value_range_body = {
                "range": range_,
                "majorDimension": major_dimesion,
                "values": data_list
            }

            try:
                request = self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheetId,
                    range=range_,
                    valueInputOption='USER_ENTERED',
                    body=value_range_body)
                response = request.execute()
                logging.info(response)
                status = True
            except googleapiclient.errors.HttpError as e:
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:  # Access Limit Crossed
                    time.sleep(60)
                    status = self.update_data_in_sheet(
                        spreadsheetId, range_, major_dimesion, data_list)
                else:
                    logging.info("googleSheetHandler.UpdateDataInSheet ::: {}".
                                 format(e))
            except Exception as e:
                logging.info(
                    "googleSheetHandler.UpdateDataInSheet ::: {}".format(e))
        else:
            logging.info(
                "googleSheetHandler.UpdateDataInSheet ::: Please enter a valid sheetID, range and data list"
            )
        return status

    def update_cell(self,
                    sheetIndex=0,
                    rowIndex=0,
                    columIndex=0,
                    data_string='',
                    delimiter='\n',
                    requests=[]):
        request = {
            "pasteData": {
                "coordinate": {
                    "sheetId": sheetIndex,
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
        return requests

    def create_border(self,
                      sheetIndex=0,
                      start_row_index=0,
                      end_row_index=10,
                      start_col_index=0,
                      end_col_index=6,
                      border_width=1,
                      border_style="SOLID",
                      color='alpha',
                      color_index=1.0,
                      requests=[]):
        request = {
            "updateBorders": {
                "range": {
                    "sheetId": sheetIndex if sheetIndex else sheetIndex,
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
        return requests

    def merge_cells(self,
                    sheetIndex=0,
                    start_row_index=0,
                    end_row_index=10,
                    start_col_index=0,
                    end_col_index=6,
                    merge_type="MERGE_COLUMNS",
                    requests=[]):
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
        return requests

    def mark_headers(self,
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
                     bold=True,
                     requests=[]):
        request = {
            "repeatCell": {
                "range": {
                    "sheetId": sheetIndex,
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
        return requests

    def data_alignment(self,
                       sheetIndex=0,
                       start_row_index=0,
                       end_row_index=1,
                       start_col_index=0,
                       end_col_index=6,
                       alignment=Format.CENTER.value,
                       wrap=Format.NO_WRAPING.value,
                       requests=[]):
        request = {
            "repeatCell": {
                "range": {
                    "sheetId": sheetIndex,
                    "startRowIndex": start_row_index,
                    "endRowIndex": end_row_index,
                    "startColumnIndex": start_col_index,
                    "endColumnIndex": end_col_index
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": alignment,
                        "wrapStrategy": wrap
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"
            }
        }
        requests.append(request)
        return requests

    def read_data_from_sheet(
            self,
            spreadsheetId=None,
            rangeName='',  # Sample Range 'Rohit!A1:F',
            numberOfColumns=0):
        values = []
        if spreadsheetId and rangeName:
            try:
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=spreadsheetId, range=rangeName).execute()
                values = result.get('values', [])

                if not values:
                    logging.info(
                        'GooglesheetHandler.ReadDataFromSheet ::: No data found.'
                    )
                else:
                    numberOfColumns = len(
                        values) if not numberOfColumns else numberOfColumns
                    for row in values[:numberOfColumns]:
                        # Print columns A to F, which correspond to indices 0 to 5.
                        logging.debug(
                            "GooglesheetHandler.ReadDataFromSheet ::: Row ::: {}".
                            format(row))
            except googleapiclient.errors.HttpError as e:
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:  # Access Limit Crossed
                    time.sleep(60)
                    values = self.read_data_from_sheet(
                        spreadsheetId, rangeName, numberOfColumns)
                else:
                    logging.info("googleSheetHandler.ReadDataFromSheet ::: {}".
                                 format(e))
            except Exception as e:
                logging.info(
                    "googleSheetHandler.ReadDataFromSheet ::: {}".format(e))
        else:
            logging.info(
                "GooglesheetHandler.ReadDataFromSheet ::: Please Enter a Valid SPreadsheetID and Range Value."
            )
        return values

    def duplicate_sheet(self,
                        sourceSheetId=0,
                        sheetIndex=1,
                        newSheetId=None,
                        newSheetName='',
                        requests=[]):
        request = {
            "duplicateSheet": {
                "sourceSheetId": sourceSheetId,
                "insertSheetIndex": sheetIndex,
                "newSheetId": newSheetId,
                "newSheetName": newSheetName
            }
        }
        requests.append(request)
        return requests

    def add_column_chart(self,
                         chartId=None,
                         sheetId=0,
                         usersCount=2,
                         requests=[]):
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
        return requests

    def add_bar_chart(self, chartId=None, sheetId=0, usersCount=2,
                      requests=[]):
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
        return requests

    def setDataValidation(self, sheetId=0, endRowIndex=129, requests=[]):
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
        return requests


if __name__ == '__main__':
    gsh = GoogleSheetHandler()
