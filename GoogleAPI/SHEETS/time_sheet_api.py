from google_sheet_handler import GoogleSheetHandler
import math
import time
import googleapiclient
import json
import cherrypy
import sys
from log_utils import OneLineExceptionFormatter
import logging


class TimeSheetAPI:
    api_start_time = time.time()
    MONTH_PARAMETER = "month"
    YEAR_PARAMETER = "year"
    SHEET_ID_PARAMETER = "spreadsheetID"
    USERS_PARAMETER = "usersNameList"
    LOG_FORMAT_STRING = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
        self.WEEK_DAYS = [
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
            'Sunday'
        ]

        self.BASE_DATE = (6, 11, 2017, self.WEEK_DAYS[0])

        self.MONTHS = [
            "January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December"
        ]
        self.PER_DAY_ROWS_COUNT = 4
        self.HEADER_ROWS_COUNT = 5
        self.gsh = GoogleSheetHandler()
        root.info("API Start Time= {}s".format(time.time() -
                                               TimeSheetAPI.api_start_time))

    def compute_number_of_days(self, month, year):
        month -= 1
        number_of_days = 31 if (month % 7) % 2 == 0 else 30
        if self.MONTHS[month] == 'February':
            number_of_days = 28
            if year % 400 == 0 or (year % 100 != 0 and year % 4 == 0):
                number_of_days += 1
        return number_of_days

    def compute_day(self, day, month, year):
        shifted_month = (month - 2) if month > 2 else (month + 10)
        last_2_digit_of_year = (year % 100) if month > 2 else (year % 100 - 1)
        first_2_digit_of_year = year / 100
        w = (
            day + int(math.floor(2.6 * shifted_month - 0.2)) +
            last_2_digit_of_year + int(math.floor(last_2_digit_of_year / 4.0))
            + int(math.floor(first_2_digit_of_year / 4.0)) - 2 *
            first_2_digit_of_year)
        w %= 7
        if w < 0:
            w += 7
        day = (w + 6) % 7
        return day

    def insert_header(self,
                      employee_id=None,
                      employee_name=None,
                      sheetIndex=0,
                      sheetName=None,
                      spreadsheet_id=None,
                      number_of_days_in_week_1=0,
                      number_of_days_in_week_5=0):
        sheetName = "Sheet{}".format(sheetIndex +
                                     1) if not sheetName else sheetName
        data = []
        start_index = self.HEADER_ROWS_COUNT + 1
        end_index = number_of_days_in_week_1 * self.PER_DAY_ROWS_COUNT + self.HEADER_ROWS_COUNT
        for _ in range(4):
            d = "=SUM(F{}:F{})".format(start_index, end_index)
            data.append(d)
            start_index = end_index + 1
            end_index += 7 * self.PER_DAY_ROWS_COUNT
        end_index = start_index + number_of_days_in_week_5 * self.PER_DAY_ROWS_COUNT - 1
        d = "=SUM(F{}:F{})".format(start_index, end_index)
        data.append(d)

        data_list = [
            [
                "Name:  {}  -  {}".format(employee_id, employee_name)
                if (employee_id and employee_name) else "Employee Name", "",
                "", "", "", ""
            ], ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", ""], data,
            ["", "", "Month", "=SUM(A3:E3)", "", ""],
            ["Day", "Date", "Project", "Task", "Hrs spent", "Total Hrs"]
        ]
        range_text = "{}!A{}:F{}".format(sheetName, 1, self.HEADER_ROWS_COUNT)
        self.gsh.update_data_in_sheet(
            spreadsheet_id=spreadsheet_id,
            range_=range_text,
            data_list=data_list)
        self.gsh.mark_headers(
            spreadsheetId=spreadsheet_id,
            start_row_index=0,
            end_row_index=1,
            red_bg_color=153,
            green_bg_color=204,
            blue_bg_color=255,
            sheetIndex=sheetIndex)
        self.gsh.mark_headers(
            spreadsheetId=spreadsheet_id,
            start_row_index=1,
            end_row_index=self.HEADER_ROWS_COUNT - 1,
            red_bg_color=238,
            green_bg_color=238,
            blue_bg_color=238,
            sheetIndex=sheetIndex)
        self.gsh.mark_headers(
            spreadsheetId=spreadsheet_id,
            start_row_index=self.HEADER_ROWS_COUNT - 1,
            end_row_index=self.HEADER_ROWS_COUNT,
            sheetIndex=sheetIndex)

    def insert_rows(self,
                    sheetIndex=0,
                    sheetName=None,
                    spreadsheet_id=None,
                    continue_day=None,
                    number_of_days=0,
                    month=0,
                    year=0):
        sheetName = "Sheet{}".format(sheetIndex +
                                     1) if not sheetName else sheetName
        start_index = self.HEADER_ROWS_COUNT + 1
        end_index = start_index + self.PER_DAY_ROWS_COUNT * number_of_days - 1
        try:
            for day in range(1, number_of_days + 1):
                if continue_day and day < continue_day:
                    start_index += self.PER_DAY_ROWS_COUNT
                    continue
                day_index = self.compute_day(day, month, year)
                row = [#'{}'.format(WEEK_DAYS[compute_day(day, month, year)]),
                       '=IF((INDIRECT(ADDRESS(ROW(),COLUMN()+1,4))<>0), TEXT(INDIRECT(ADDRESS(ROW(),COLUMN()+1,4)), "dddd"), "")',
                       '{}/{}/{}'.format(month, day, year),
                       "", "", "", "=SUM(E{}:E{})".format(start_index, start_index+self.PER_DAY_ROWS_COUNT-1)]
                data_list = [["", "", "", "", "", ""]
                             if i + 1 < self.PER_DAY_ROWS_COUNT else row
                             for i in range(self.PER_DAY_ROWS_COUNT)]
                range_text = "{}!A{}:F{}".format(
                    sheetName, start_index,
                    start_index + self.PER_DAY_ROWS_COUNT - 1)
                self.gsh.update_data_in_sheet(
                    spreadsheet_id=spreadsheet_id,
                    range_=range_text,
                    data_list=data_list)
                self.gsh.merge_cells(
                    spreadsheetId=spreadsheet_id,
                    start_row_index=start_index - 1,
                    end_row_index=start_index + self.PER_DAY_ROWS_COUNT - 1,
                    start_col_index=0,
                    end_col_index=2,
                    sheetIndex=sheetIndex)
                self.gsh.merge_cells(
                    spreadsheetId=spreadsheet_id,
                    start_row_index=start_index - 1,
                    end_row_index=start_index + self.PER_DAY_ROWS_COUNT - 1,
                    start_col_index=5,
                    end_col_index=6,
                    sheetIndex=sheetIndex)
                if day_index in set([5, 6]):
                    self.gsh.mark_headers(
                        spreadsheetId=spreadsheet_id,
                        start_row_index=start_index - 1,
                        end_row_index=start_index + self.PER_DAY_ROWS_COUNT -
                        1,
                        red_bg_color=204,
                        green_bg_color=255,
                        blue_bg_color=204,
                        bold=False,
                        sheetIndex=sheetIndex)
                start_index += self.PER_DAY_ROWS_COUNT

            data_list = [[
                "", "", "", "Total Hours", "",
                "=SUM(F{}:F{})".format(self.HEADER_ROWS_COUNT + 1, end_index)
            ]]
            range_text = "{}!A{}:F{}".format(sheetName, start_index,
                                             start_index)
            self.gsh.update_data_in_sheet(
                spreadsheet_id=spreadsheet_id,
                range_=range_text,
                data_list=data_list)
            self.gsh.mark_headers(
                spreadsheetId=spreadsheet_id,
                start_row_index=end_index,
                end_row_index=end_index + 1,
                sheetIndex=sheetIndex)
        except googleapiclient.errors.HttpError as e:
            print e
            try:
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:
                    time.sleep(60)
                    self.insert_rows(
                        sheetIndex=sheetIndex,
                        sheetName=sheetName,
                        spreadsheet_id=spreadsheet_id,
                        continue_day=day,
                        number_of_days=number_of_days,
                        month=month,
                        year=year)
                else:
                    raise Exception(e)
            except Exception as e:
                raise Exception(e)

    def add_weekly_sheet(self,
                         sheetIndex=0,
                         sheetName=None,
                         users=[],
                         spreadsheet_id=None):
        sheetName = "Sheet{}".format(sheetIndex +
                                     1) if not sheetName else sheetName

        data_list = []
        data_list.append([""] + users + ["Total"])
        data_list.append(["Week 1"] + [
            "='{}'!A3".format(user) for user in users
        ] + ["=sum(A2:{}2)".format(chr(ord("A") + len(users)))])
        data_list.append(["Week 2"] + [
            "='{}'!B3".format(user) for user in users
        ] + ["=sum(A3:{}3)".format(chr(ord("A") + len(users)))])
        data_list.append(["Week 3"] + [
            "='{}'!C3".format(user) for user in users
        ] + ["=sum(A4:{}4)".format(chr(ord("A") + len(users)))])
        data_list.append(["Week 4"] + [
            "='{}'!D3".format(user) for user in users
        ] + ["=sum(A5:{}5)".format(chr(ord("A") + len(users)))])
        data_list.append(["Week 5"] + [
            "='{}'!E3".format(user) for user in users
        ] + ["=sum(A6:{}6)".format(chr(ord("A") + len(users)))])
        data_list.append(["Sum"] + [
            "=sum({}2:{}6)".format(
                chr(ord("A") + i + 1), chr(ord("A") + i + 1))
            for i, user in enumerate(users)
        ] + [
            "=sum({}2:{}6)".format(
                chr(ord("A") + len(users) + 1), chr(ord("A") + len(users) + 1))
        ])

        range_text = "{}!A1:{}7".format(sheetName,
                                        chr(ord("A") + len(users) + 1))

        self.gsh.create_border(
            spreadsheetId=spreadsheet_id,
            sheetIndex=sheetIndex,
            end_row_index=7,
            end_col_index=len(users) + 2)

        self.gsh.update_data_in_sheet(
            spreadsheet_id=spreadsheet_id,
            range_=range_text,
            data_list=data_list)

        r, g, b = self.get_rgb_from_hex(color_hex="673AB7")
        self.gsh.mark_headers(
            spreadsheetId=spreadsheet_id,
            start_col_index=1,
            end_col_index=len(users) + 2,
            red_bg_color=r,
            green_bg_color=g,
            blue_bg_color=b,
            red_fg_color=255.0,
            green_fg_color=255.0,
            blue_fg_color=255.0,
            sheetIndex=sheetIndex)

        self.gsh.mark_headers(
            spreadsheetId=spreadsheet_id,
            sheetIndex=sheetIndex,
            start_row_index=6,
            end_row_index=7,
            start_col_index=0,
            end_col_index=len(users) + 2,
            red_bg_color=255,
            green_bg_color=255,
            blue_bg_color=255,
            base_color=255.0,
            red_fg_color=0.0,
            green_fg_color=0.0,
            blue_fg_color=0.0,
            bold=True)

    def add_sprint_hrs_sheet(self,
                             sheetIndex=0,
                             sheetName=None,
                             users=[],
                             end_index=129,
                             spreadsheet_id=None):
        sheetName = "Sheet{}".format(sheetIndex +
                                     1) if not sheetName else sheetName

        data_list = []
        data_list.append(["Project"] + users)
        data_list.append(["=SORT(Projects!A:A, 1, 1)"] + [
            "=SUMIF('{}'!$C$6:$C${},$A{},'{}'!$E$6:$E${})".format(
                user, 129, 2, user, 129) for user in users
        ])
        data_list.append([""] + [
            "=SUMIF('{}'!$C$6:$C${},$A{},'{}'!$E$6:$E${})".format(
                user, end_index, 3, user, end_index) for user in users
        ])
        data_list.append([""] + [
            "=SUMIF('{}'!$C$6:$C${},$A{},'{}'!$E$6:$E${})".format(
                user, end_index, 4, user, end_index) for user in users
        ])
        data_list.append([""] + [
            "=SUMIF('{}'!$C$6:$C${},$A{},'{}'!$E$6:$E${})".format(
                user, end_index, 5, user, end_index) for user in users
        ])
        data_list.append([""] + [
            "=SUMIF('{}'!$C$6:$C${},$A{},'{}'!$E$6:$E${})".format(
                user, end_index, 6, user, end_index) for user in users
        ])
        data_list.append([""] + ["" for user in users])
        data_list.append([""] + ["" for user in users])
        data_list.append([""] + [
            "=sum({}3:{}8)".format(
                chr(ord("A") + i + 1), chr(ord("A") + i + 1))
            for i, user in enumerate(users)
        ])

        range_text = "{}!A1:{}9".format(sheetName, chr(ord("A") + len(users)))

        self.gsh.create_border(
            spreadsheetId=spreadsheet_id,
            sheetIndex=sheetIndex,
            end_row_index=9,
            end_col_index=len(users) + 1)

        self.gsh.update_data_in_sheet(
            spreadsheet_id=spreadsheet_id,
            range_=range_text,
            data_list=data_list)

        r, g, b = self.get_rgb_from_hex(color_hex="B39DDB")
        self.gsh.mark_headers(
            spreadsheetId=spreadsheet_id,
            end_col_index=len(users) + 1,
            red_bg_color=r,
            green_bg_color=g,
            blue_bg_color=b,
            red_fg_color=255.0,
            green_fg_color=255.0,
            blue_fg_color=255.0,
            sheetIndex=sheetIndex)

    def get_rgb_from_hex(self, color_hex="4A148C"):
        a = [
            int(x) if ("0" <= x <= "9") else (10 + ord(x) - ord("A"))
            for x in color_hex
        ]
        print a
        r = a[0] * 16 + a[1]
        g = a[2] * 16 + a[3]
        b = a[4] * 16 + a[5]
        return (r, g, b)

    def add_projects_sheet(self,
                           sheetIndex=0,
                           sheetName=None,
                           projects=[
                               "Client communication", "Documentation", "R&D",
                               "Team meeting", "Zippia"
                           ],
                           spreadsheet_id=None):
        sheetName = "Sheet{}".format(sheetIndex +
                                     1) if not sheetName else sheetName

        data_list = []
        [data_list.append([project]) for project in projects]

        range_text = "{}!A1:A{}".format(sheetName, len(projects))

        self.gsh.update_data_in_sheet(
            spreadsheet_id=spreadsheet_id,
            range_=range_text,
            data_list=data_list)

    def sheet_processor(self, month, year, sheets, spreadsheet_id=None):
        number_of_days = self.compute_number_of_days(month, year)
        day = self.compute_day(1, month, year)
        number_of_days_in_week_1 = (7 - day)  #if day < 5 else 7
        number_of_days_in_week_5 = number_of_days - 21 - number_of_days_in_week_1
        end_index = self.HEADER_ROWS_COUNT + 1 + self.PER_DAY_ROWS_COUNT * number_of_days

        if not spreadsheet_id:
            while True:
                print "Creating a new spreadsheet...."
                try:
                    spreadsheet_id = self.gsh.create_google_sheet()[
                        "spreadsheetId"]
                    break
                except googleapiclient.errors.HttpError as e:
                    print e
                    try:
                        data = json.loads(e.content.decode('utf-8'))
                        if data['error']['code'] == 429:
                            time.sleep(60)
                            continue
                        else:
                            break
                    except:
                        break
                except Exception as e:
                    print e
                    break

        for sheet_index, sheet_name in enumerate(sheets):
            if sheet_index:
                while True:
                    print "Adding {} Sheet..".format(sheet_name)
                    try:
                        self.gsh.duplicate_sheet(
                            spreadsheetId=spreadsheet_id,
                            sheetIndex=sheet_index,
                            newSheetId=sheet_index,
                            newSheetName=sheet_name)
                        break
                    except googleapiclient.errors.HttpError as e:
                        print e
                        data = json.loads(e.content.decode('utf-8'))
                        if data['error']['code'] == 429:
                            time.sleep(60)
                            continue
            else:
                while True:
                    print "Creating Border in First Sheet"
                    try:
                        self.gsh.create_border(
                            spreadsheetId=spreadsheet_id,
                            end_row_index=end_index,
                            sheetIndex=sheet_index)
                        break
                    except googleapiclient.errors.HttpError as e:
                        print e
                        data = json.loads(e.content.decode('utf-8'))
                        if data['error']['code'] == 429:
                            time.sleep(60)
                            continue
                while True:
                    print "Adding headers in First Sheet.."
                    try:
                        self.insert_header(
                            sheetIndex=sheet_index,
                            sheetName=sheet_name,
                            spreadsheet_id=spreadsheet_id,
                            number_of_days_in_week_1=number_of_days_in_week_1,
                            number_of_days_in_week_5=number_of_days_in_week_5)
                        break
                    except googleapiclient.errors.HttpError as e:
                        print e
                        data = json.loads(e.content.decode('utf-8'))
                        if data['error']['code'] == 429:
                            time.sleep(60)
                            continue
                self.insert_rows(
                    sheetIndex=sheet_index,
                    sheetName=sheet_name,
                    spreadsheet_id=spreadsheet_id,
                    continue_day=None,
                    number_of_days=number_of_days,
                    month=month,
                    year=year)

        sheet_index += 1
        SHEET, DATA = True, True
        while SHEET or DATA:
            print "Adding Projects Sheet"
            try:
                if SHEET:
                    self.gsh.add_sheet(
                        spreadsheetId=spreadsheet_id,
                        sheetIndex=sheet_index,
                        sheetName="Projects")
                    SHEET = False
                if not SHEET and DATA:
                    self.add_projects_sheet(
                        sheet_index, "Projects", spreadsheet_id=spreadsheet_id)
                    DATA = False
            except googleapiclient.errors.HttpError as e:
                print e
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:
                    time.sleep(60)
                    continue
        i = 0
        while i < len(sheets):
            print "Adding Data Validations"
            try:
                self.gsh.setDataValidation(
                    spreadsheetId=spreadsheet_id,
                    sheetId=i,
                    endRowIndex=end_index - 1)
                i += 1
            except googleapiclient.errors.HttpError as e:
                print e
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:
                    time.sleep(60)
                    continue

        sheet_index += 1
        SHEET, DATA = True, True
        while SHEET or DATA:
            print "Adding Weekly Sheet"
            try:
                if SHEET:
                    self.gsh.add_sheet(
                        spreadsheetId=spreadsheet_id,
                        sheetIndex=sheet_index,
                        sheetName="Weekly")
                    SHEET = False
                if not SHEET and DATA:
                    self.add_weekly_sheet(
                        sheet_index,
                        "Weekly",
                        sheets[1:],
                        spreadsheet_id=spreadsheet_id)
                    DATA = False
            except googleapiclient.errors.HttpError as e:
                print e
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:
                    time.sleep(60)
                    continue

        while True:
            print "Adding Weekly Column Chart in Sheet"
            try:
                self.gsh.add_column_chart(
                    spreadsheetId=spreadsheet_id,
                    sheetId=sheet_index + 1,
                    usersCount=len(sheets) - 1)
                break
            except googleapiclient.errors.HttpError as e:
                print e
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:
                    time.sleep(60)
                    continue

        sheet_index += 1
        SHEET, DATA = True, True
        while SHEET or DATA:
            print "Adding Sprint - Hrs Sheet"
            try:
                if SHEET:
                    self.gsh.add_sheet(
                        spreadsheetId=spreadsheet_id,
                        sheetIndex=sheet_index,
                        sheetName="Sprint - Hrs")
                    SHEET = False
                if not SHEET and DATA:
                    self.add_sprint_hrs_sheet(
                        sheet_index,
                        "Sprint - Hrs",
                        sheets[1:],
                        end_index=end_index,
                        spreadsheet_id=spreadsheet_id)
                    DATA = False
            except googleapiclient.errors.HttpError as e:
                print e
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:
                    time.sleep(60)
                    continue

        while True:
            print "Adding Sprint Bar Chart in Sheet"
            try:
                self.gsh.add_bar_chart(
                    spreadsheetId=spreadsheet_id,
                    sheetId=sheet_index + 1,
                    usersCount=len(sheets) - 1)
                break
            except googleapiclient.errors.HttpError as e:
                print e
                data = json.loads(e.content.decode('utf-8'))
                if data['error']['code'] == 429:
                    time.sleep(60)
                    continue

        return spreadsheet_id

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def create(self, **other_params):
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.headers['Connection'] = "close"

        params = {}
        if cherrypy.request.method == "POST":
            params = cherrypy.request.json
        error_message = "Missing Required Parameter"
        total_time = time.time()
        month = params[
            TimeSheetAPI.
            MONTH_PARAMETER] if TimeSheetAPI.MONTH_PARAMETER in params else None
        year = params[
            TimeSheetAPI.
            YEAR_PARAMETER] if TimeSheetAPI.YEAR_PARAMETER in params else time.localtime(
            )[0]
        sheets = params[
            TimeSheetAPI.
            USERS_PARAMETER] if TimeSheetAPI.USERS_PARAMETER in params else []
        spreadsheet_id = params[
            TimeSheetAPI.
            SHEET_ID_PARAMETER] if TimeSheetAPI.SHEET_ID_PARAMETER in params else None

        sheets.insert(0, None)
        if month:
            spreadsheet_id = self.sheet_processor(
                month=month,
                year=year,
                sheets=sheets,
                spreadsheet_id=spreadsheet_id)
            response_object = {
                "processingTime": time.time() - total_time,
                "spreadsheetID": spreadsheet_id
            }
        else:
            response_object = {error_message: error_message}
        return response_object


class health_check:
    def __init__(self):
        self.init_time = int(time.time() * 1000)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def heartbeat(self, **params):
        current_time = int(time.time() * 1000)
        stats = {}
        response_json = {}
        response_json["upTime"] = self.init_time
        response_json["currentTime"] = current_time
        response_json["stats"] = stats
        return response_json


''' Initializing the web server '''
if __name__ == '__main__':
    logging_handler = logging.StreamHandler(sys.stdout)
    log_format = OneLineExceptionFormatter(TimeSheetAPI.LOG_FORMAT_STRING,
                                           TimeSheetAPI.LOG_TIME_FORMAT)
    logging_handler.setFormatter(log_format)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(logging_handler)
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,
        'server.thread_pool_max': 1,
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'response.timeout': 600,
        'server.socket_queue_size': 10,
        'engine.timeout_monitor.on': False,
        'log.screen': False,
        'log.access_file': '',
        'log.error_log_propagate': False,
        'log.accrss_log.propagate': False,
        'log.error_file': ''
    })

    cherrypy.tree.mount(
        TimeSheetAPI(),
        '/timeSheet',  #configurator.commons.JOB_NORMALIZATION_API_CONTEXT,
        config={'/': {}})
    cherrypy.tree.mount(health_check(), '/', config={'/': {}})
    cherrypy.engine.start()
    cherrypy.engine.block()
