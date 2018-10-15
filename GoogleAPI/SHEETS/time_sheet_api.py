from google_sheet_handler import GoogleSheetHandler, Format
import math
import time
import cherrypy
import sys
from log_utils import OneLineExceptionFormatter
import logging
from db_utils import mongoDB
import config


class TimeSheetAPI:
    MONTH_PARAMETER = "month"
    YEAR_PARAMETER = "year"
    SHEET_ID_PARAMETER = "spreadsheetID"
    USERS_PARAMETER = "usersList"
    USERNAME_PARAMETER = "userName"
    USER_EMAIL_PARAMETER = "userEmailAddr"
    USER_ID_PARAMETER = "userID"
    PROJECT_NAME_PARAMETER = "projectName"
    ADMIN_EMAIL_PARAMETER = "adminEmailAddr"
    MARKING_TYPE_PARAMETER = "markingType"
    MARKING_DATES_PARAMETER = "markingDates"
    MARKING_SHEET_NAME_PARAMETER = "markingSheetName"
    MARKING_SHEET_INDEX_PARAMETER = "markingSheetIndex"
    LEAVE_MARKING = "leave"
    WORKDAY_MARKING = "working"
    HOLIDAY_MARKING = "holiday"

    api_start_time = time.time()
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
        self.leave_hex = "FFFF00"
        self.holiday_hex = "CCFFCC"
        self.workday_hex = "FFFFFF"

        self.common_project_fields = [
            "Client communication", "Documentation", "R&D", "Team meeting"
        ]
        self.default_project_name = "ProjectName"

        # Initialize MongoDB instance
        self.mongodb = mongoDB()

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
                      number_of_days_in_week_5=0,
                      requests=[]):
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
            spreadsheetId=spreadsheet_id,
            range_=range_text,
            data_list=data_list)
        requests = self.gsh.mark_headers(
            start_row_index=0,
            end_row_index=1,
            red_bg_color=153,
            green_bg_color=204,
            blue_bg_color=255,
            sheetIndex=sheetIndex,
            requests=requests)
        requests = self.gsh.mark_headers(
            start_row_index=1,
            end_row_index=self.HEADER_ROWS_COUNT - 1,
            red_bg_color=238,
            green_bg_color=238,
            blue_bg_color=238,
            sheetIndex=sheetIndex,
            requests=requests)
        requests = self.gsh.mark_headers(
            start_row_index=self.HEADER_ROWS_COUNT - 1,
            end_row_index=self.HEADER_ROWS_COUNT,
            sheetIndex=sheetIndex,
            requests=requests)
        return requests

    def insert_rows(self,
                    sheetIndex=0,
                    sheetName=None,
                    spreadsheet_id=None,
                    continue_day=None,
                    number_of_days=0,
                    month=0,
                    year=0,
                    requests=[]):
        sheetName = "Sheet{}".format(sheetIndex +
                                     1) if not sheetName else sheetName
        start_index = self.HEADER_ROWS_COUNT + 1
        end_index = start_index + self.PER_DAY_ROWS_COUNT * number_of_days - 1
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
                spreadsheetId=spreadsheet_id,
                range_=range_text,
                data_list=data_list)
            requests = self.gsh.merge_cells(
                start_row_index=start_index - 1,
                end_row_index=start_index + self.PER_DAY_ROWS_COUNT - 1,
                start_col_index=0,
                end_col_index=2,
                sheetIndex=sheetIndex,
                requests=requests)
            requests = self.gsh.merge_cells(
                start_row_index=start_index - 1,
                end_row_index=start_index + self.PER_DAY_ROWS_COUNT - 1,
                start_col_index=5,
                end_col_index=6,
                sheetIndex=sheetIndex,
                requests=requests)
            if day_index in set([5, 6]):
                requests = self.gsh.mark_headers(
                    start_row_index=start_index - 1,
                    end_row_index=start_index + self.PER_DAY_ROWS_COUNT - 1,
                    red_bg_color=204,
                    green_bg_color=255,
                    blue_bg_color=204,
                    bold=False,
                    sheetIndex=sheetIndex,
                    requests=requests)
            start_index += self.PER_DAY_ROWS_COUNT

        data_list = [[
            "", "", "", "Total Hours", "",
            "=SUM(F{}:F{})".format(self.HEADER_ROWS_COUNT + 1, end_index)
        ]]
        range_text = "{}!A{}:F{}".format(sheetName, start_index, start_index)
        self.gsh.update_data_in_sheet(
            spreadsheetId=spreadsheet_id,
            range_=range_text,
            data_list=data_list)
        requests = self.gsh.mark_headers(
            start_row_index=end_index,
            end_row_index=end_index + 1,
            sheetIndex=sheetIndex,
            requests=requests)
        return requests

    def add_weekly_sheet(self,
                         sheetIndex=0,
                         sheetName=None,
                         users=[],
                         spreadsheet_id=None,
                         requests=[]):
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

        self.gsh.update_data_in_sheet(
            spreadsheetId=spreadsheet_id,
            range_=range_text,
            data_list=data_list)

        requests = self.gsh.create_border(
            sheetIndex=sheetIndex,
            end_row_index=7,
            end_col_index=len(users) + 2,
            requests=requests)

        r, g, b = self.get_rgb_from_hex(color_hex="673AB7")
        requests = self.gsh.mark_headers(
            start_col_index=1,
            end_col_index=len(users) + 2,
            red_bg_color=r,
            green_bg_color=g,
            blue_bg_color=b,
            red_fg_color=255.0,
            green_fg_color=255.0,
            blue_fg_color=255.0,
            sheetIndex=sheetIndex,
            requests=requests)

        requests = self.gsh.mark_headers(
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
            bold=True,
            requests=requests)
        return requests

    def add_sprint_hrs_sheet(self,
                             sheetIndex=0,
                             sheetName=None,
                             users=[],
                             end_index=129,
                             spreadsheet_id=None,
                             requests=[]):
        sheetName = "Sheet{}".format(sheetIndex +
                                     1) if not sheetName else sheetName

        data_list = []
        data_list.append(["Project"] + users)
        data_list.append(["=SORT(Projects!A:A, 1, 1)"] + [
            "=SUMIF('{}'!$C$6:$C${},$A{},'{}'!$E$6:$E${})".format(
                user, end_index, 2, user, end_index) for user in users
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

        self.gsh.update_data_in_sheet(
            spreadsheetId=spreadsheet_id,
            range_=range_text,
            data_list=data_list)

        requests = self.gsh.create_border(
            sheetIndex=sheetIndex,
            end_row_index=9,
            end_col_index=len(users) + 1,
            requests=requests)

        r, g, b = self.get_rgb_from_hex(color_hex="B39DDB")
        requests = self.gsh.mark_headers(
            end_col_index=len(users) + 1,
            red_bg_color=r,
            green_bg_color=g,
            blue_bg_color=b,
            red_fg_color=255.0,
            green_fg_color=255.0,
            blue_fg_color=255.0,
            sheetIndex=sheetIndex,
            requests=requests)
        return requests

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
                           projects=[],
                           spreadsheet_id=None):
        sheetName = "Sheet{}".format(sheetIndex +
                                     1) if not sheetName else sheetName

        data_list = []
        [data_list.append([project]) for project in projects]

        range_text = "{}!A1:A{}".format(sheetName, len(projects))

        self.gsh.update_data_in_sheet(
            spreadsheetId=spreadsheet_id,
            range_=range_text,
            data_list=data_list)

    def sheet_processor(self,
                        month,
                        year,
                        sheets,
                        project_name=None,
                        spreadsheet_id=None):
        number_of_days = self.compute_number_of_days(month, year)
        day = self.compute_day(1, month, year)
        number_of_days_in_week_1 = (7 - day)  #if day < 5 else 7
        number_of_days_in_week_5 = number_of_days - 21 - number_of_days_in_week_1
        end_index = self.HEADER_ROWS_COUNT + 1 + self.PER_DAY_ROWS_COUNT * number_of_days

        if not spreadsheet_id:
            print "Creating a new spreadsheet...."
            create_response = self.gsh.create_google_sheet(
                projectName=project_name,
                month=self.MONTHS[month - 1],
                year=year)
            if create_response:
                spreadsheet_id = create_response["spreadsheetId"]
            else:
                return None

        requests = []
        for sheet_index, sheet_name in enumerate(sheets):
            if sheet_index:
                print "Adding {} Sheet..".format(sheet_name)
                requests = self.gsh.duplicate_sheet(
                    sheetIndex=sheet_index,
                    newSheetId=sheet_index,
                    newSheetName=sheet_name,
                    requests=requests)
            else:
                print "Adding Borders in First Sheet..."
                requests = self.gsh.create_border(
                    end_row_index=end_index,
                    sheetIndex=sheet_index,
                    requests=requests)
                print "Adding headers in First Sheet.."
                requests = self.insert_header(
                    sheetIndex=sheet_index,
                    sheetName=sheet_name,
                    spreadsheet_id=spreadsheet_id,
                    number_of_days_in_week_1=number_of_days_in_week_1,
                    number_of_days_in_week_5=number_of_days_in_week_5,
                    requests=requests)
                requests = self.insert_rows(
                    sheetIndex=sheet_index,
                    sheetName=sheet_name,
                    spreadsheet_id=spreadsheet_id,
                    continue_day=None,
                    number_of_days=number_of_days,
                    month=month,
                    year=year,
                    requests=requests)
                requests = self.gsh.data_alignment(
                    sheetIndex=sheet_index,
                    end_row_index=end_index,
                    alignment=Format.CENTER.value,
                    requests=requests)
                requests = self.gsh.data_alignment(
                    sheetIndex=sheet_index,
                    start_row_index=self.HEADER_ROWS_COUNT,
                    end_row_index=end_index - 1,
                    start_col_index=3,
                    end_col_index=4,
                    alignment=Format.LEFT.value,
                    wrap=Format.WRAP.value,
                    requests=requests)
                requests = self.gsh.data_alignment(
                    sheetIndex=sheet_index,
                    end_col_index=1,
                    alignment=Format.CENTER.value,
                    wrap=Format.WRAP.value,
                    requests=requests)
        status, response = self.gsh.process_batch_requests(
            spreadsheetId=spreadsheet_id, requests=requests)
        logging.info({
            "status": status,
            "response": response,
            "msg": "SheetProcessor ::: Create User Sheets"
        })

        sheet_index += 1
        print "Adding Projects Sheet"
        requests = self.gsh.add_sheet(
            sheetIndex=sheet_index, sheetName="Projects", requests=[])
        status, response = self.gsh.process_batch_requests(
            spreadsheetId=spreadsheet_id, requests=requests)
        if status:
            self.add_projects_sheet(
                sheet_index,
                "Projects",
                projects=self.common_project_fields +
                [project_name if project_name else self.default_project_name],
                spreadsheet_id=spreadsheet_id)

        i = 0
        requests = []
        print "Adding Data Validations"
        while i < len(sheets):
            requests = self.gsh.setDataValidation(
                sheetId=i, endRowIndex=end_index - 1, requests=requests)
            i += 1
        self.gsh.process_batch_requests(
            spreadsheetId=spreadsheet_id, requests=requests)

        sheet_index += 1
        print "Adding Weekly Sheet at sheetIndex: {}".format(sheet_index)
        requests = self.gsh.add_sheet(
            sheetIndex=sheet_index, sheetName="Weekly", requests=[])
        status, response = self.gsh.process_batch_requests(
            spreadsheetId=spreadsheet_id, requests=requests)
        if status:
            requests = self.add_weekly_sheet(
                sheet_index,
                "Weekly",
                sheets[1:],
                spreadsheet_id=spreadsheet_id,
                requests=[])

            requests = self.gsh.data_alignment(
                sheetIndex=sheet_index,
                start_row_index=1,
                end_row_index=6,
                start_col_index=1,
                end_col_index=len(sheets) + 2,
                alignment=Format.CENTER.value,
                requests=requests)

            print "Adding Weekly Column Chart in Sheet"
            requests = self.gsh.add_column_chart(
                sheetId=sheet_index,
                usersCount=len(sheets) - 1,
                requests=requests)

            self.gsh.process_batch_requests(
                spreadsheetId=spreadsheet_id, requests=requests)

        sheet_index += 1
        print "Adding Sprint - Hrs Sheet at sheetIndex: {}".format(sheet_index)
        requests = self.gsh.add_sheet(
            sheetIndex=sheet_index, sheetName="Sprint - Hrs", requests=[])
        status, response = self.gsh.process_batch_requests(
            spreadsheetId=spreadsheet_id, requests=requests)
        if status:
            requests = self.add_sprint_hrs_sheet(
                sheet_index,
                "Sprint - Hrs",
                sheets[1:],
                end_index=end_index,
                spreadsheet_id=spreadsheet_id,
                requests=[])

            print "Adding Sprint Bar Chart in Sheet"
            requests = self.gsh.add_bar_chart(
                sheetId=sheet_index,
                usersCount=len(sheets) - 1,
                requests=requests)

            self.gsh.process_batch_requests(
                spreadsheetId=spreadsheet_id, requests=requests)

        return spreadsheet_id

    def update_user_details(self, users, spreadsheet_id):
        for user in users:
            self.gsh.update_data_in_sheet(
                spreadsheetId=spreadsheet_id,
                range_="{}!A1:A1".format(user[
                    TimeSheetAPI.USERNAME_PARAMETER]),
                data_list=[[
                    "Name:  {}  -  {}".format(
                        user[TimeSheetAPI.USER_ID_PARAMETER]
                        if TimeSheetAPI.USER_ID_PARAMETER in user else "",
                        user[TimeSheetAPI.USERNAME_PARAMETER])
                ]])
            ''' Share Sheet with User '''
            self.gsh.share_google_spreadsheet(
                share_emails=[
                    user[TimeSheetAPI.USER_EMAIL_PARAMETER] for user in users
                    if TimeSheetAPI.USER_EMAIL_PARAMETER in user
                ],
                spreadsheetId=spreadsheet_id)

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
            MONTH_PARAMETER] if TimeSheetAPI.MONTH_PARAMETER in params else time.localtime(
            )[1]
        year = params[
            TimeSheetAPI.
            YEAR_PARAMETER] if TimeSheetAPI.YEAR_PARAMETER in params else time.localtime(
            )[0]
        users = params[
            TimeSheetAPI.
            USERS_PARAMETER] if TimeSheetAPI.USERS_PARAMETER in params else []
        spreadsheet_id = params[
            TimeSheetAPI.
            SHEET_ID_PARAMETER] if TimeSheetAPI.SHEET_ID_PARAMETER in params else None
        adminEmail = params[
            TimeSheetAPI.
            ADMIN_EMAIL_PARAMETER] if TimeSheetAPI.ADMIN_EMAIL_PARAMETER in params else None
        projectName = params[
            TimeSheetAPI.
            PROJECT_NAME_PARAMETER] if TimeSheetAPI.PROJECT_NAME_PARAMETER in params else None

        users = [
            user for user in users if TimeSheetAPI.USERNAME_PARAMETER in user
        ]
        sheets = [user[TimeSheetAPI.USERNAME_PARAMETER] for user in users]
        sheets.insert(0, None)
        if month:
            spreadsheet_id = self.sheet_processor(
                month=month,
                year=year,
                sheets=sheets,
                project_name=projectName,
                spreadsheet_id=spreadsheet_id)
            response_object = {
                "processingTime": time.time() - total_time,
                "spreadsheetID": spreadsheet_id
            }
            self.mongodb.update_data(
                collection_name=config.TIMESHEET_COLLECTION,
                query={config.SPREADSHEET_ID: spreadsheet_id},
                update_dict={
                    "$set": {
                        config.MONTH: month,
                        config.YEAR: year,
                        config.PROJECT_NAME: projectName,
                        config.ADMIN: None,
                        config.ADMIN_EMAIL: adminEmail,
                        config.USERS_LIST: [{
                            config.USERNAME:
                            user[TimeSheetAPI.USERNAME_PARAMETER],
                            config.USER_SHEET_INDEX: i + 1,
                            config.USER_EMAIL:
                            user[TimeSheetAPI.USER_EMAIL_PARAMETER]
                            if TimeSheetAPI.USER_EMAIL_PARAMETER in user else
                            None,
                            config.USER_ID:
                            user[TimeSheetAPI.USER_ID_PARAMETER] if
                            TimeSheetAPI.USER_ID_PARAMETER in user else None,
                            config.USER_LEAVES: [],
                            config.USER_SPECIAL_WORKING_DAYS: []
                        } for i, user in enumerate(users)]
                    }
                },
                upsert=True,
                multi=False)
            self.update_user_details(users, spreadsheet_id)
        else:
            response_object = {"error_message": error_message}
        return response_object

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def mark_entry(self, **other_params):
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.headers['Connection'] = "close"

        params = {}
        if cherrypy.request.method == "POST":
            params = cherrypy.request.json
        error_message = "Missing Required Parameters ({} and {} and {} and {})".format(
            TimeSheetAPI.SHEET_ID_PARAMETER,
            TimeSheetAPI.MARKING_SHEET_INDEX_PARAMETER,
            TimeSheetAPI.MARKING_TYPE_PARAMETER,
            TimeSheetAPI.MARKING_DATES_PARAMETER)
        total_time = time.time()
        spreadsheet_id = params[
            TimeSheetAPI.
            SHEET_ID_PARAMETER] if TimeSheetAPI.SHEET_ID_PARAMETER in params else None
        sheetName = params[
            TimeSheetAPI.
            MARKING_SHEET_NAME_PARAMETER] if TimeSheetAPI.MARKING_SHEET_NAME_PARAMETER in params else None
        sheetIndex = params[
            TimeSheetAPI.
            MARKING_SHEET_INDEX_PARAMETER] if TimeSheetAPI.MARKING_SHEET_INDEX_PARAMETER in params else None
        markingType = params[
            TimeSheetAPI.
            MARKING_TYPE_PARAMETER] if TimeSheetAPI.MARKING_TYPE_PARAMETER in params else None
        markingDates = params[
            TimeSheetAPI.
            MARKING_DATES_PARAMETER] if TimeSheetAPI.MARKING_DATES_PARAMETER in params else []
        adminEmail = params[
            TimeSheetAPI.
            ADMIN_EMAIL_PARAMETER] if TimeSheetAPI.ADMIN_EMAIL_PARAMETER in params else None
        projectName = params[
            TimeSheetAPI.
            PROJECT_NAME_PARAMETER] if TimeSheetAPI.PROJECT_NAME_PARAMETER in params else None
        month = params[
            TimeSheetAPI.
            MONTH_PARAMETER] if TimeSheetAPI.MONTH_PARAMETER in params else time.localtime(
            )[1]
        year = params[
            TimeSheetAPI.
            YEAR_PARAMETER] if TimeSheetAPI.YEAR_PARAMETER in params else time.localtime(
            )[0]

        if not spreadsheet_id and adminEmail:
            spreadsheet_id = self.mongodb.fetch_spreadsheet_id(
                month, year, email=adminEmail, project=projectName)
            if not spreadsheet_id:
                error_message = "Required parameter spreadsheetID or (adminEmail and projectName)"

        if not sheetIndex and sheetName and spreadsheet_id:
            existing_sheets = self.gsh.get_all_existing_sheet_indexes(
                spreadsheetId=spreadsheet_id)
            if sheetName in set(existing_sheets.values()):
                for sheet_index, sheet_name in existing_sheets.items():
                    if sheet_name == sheetName:
                        sheetIndex = sheet_index
                        break
            if not sheetIndex:
                error_message = "Required Parameter valid sheetName or sheetIndex"

        if spreadsheet_id and sheetIndex and markingType and markingDates:
            if markingType == TimeSheetAPI.LEAVE_MARKING:
                r, g, b = self.get_rgb_from_hex(self.leave_hex)
                self.mongodb.update_data(
                    collection_name=config.TIMESHEET_COLLECTION,
                    query={config.SPREADSHEET_ID: spreadsheet_id},
                    update_dict={
                        "$addToSet": {
                            "{}.{}.{}".format(config.USERS_LIST,
                                              sheetIndex - 1,
                                              config.USER_LEAVES): {
                                                  "$each": markingDates
                                              }
                        }
                    },
                    upsert=False,
                    multi=False)
            elif markingType == TimeSheetAPI.HOLIDAY_MARKING:
                r, g, b = self.get_rgb_from_hex(self.holiday_hex)
            elif markingType == TimeSheetAPI.WORKDAY_MARKING:
                r, g, b = self.get_rgb_from_hex(self.workday_hex)
                self.mongodb.update_data(
                    collection_name=config.TIMESHEET_COLLECTION,
                    query={config.SPREADSHEET_ID: spreadsheet_id},
                    update_dict={
                        "$addToSet": {
                            "{}.{}.{}".format(
                                config.USERS_LIST, sheetIndex - 1,
                                config.USER_SPECIAL_WORKING_DAYS): {
                                    "$each": markingDates
                                }
                        }
                    },
                    upsert=False,
                    multi=False)

            requests = []
            for date in markingDates:
                if date < 1:
                    continue
                start_index = self.HEADER_ROWS_COUNT + 1 + self.PER_DAY_ROWS_COUNT * (
                    date - 1)
                requests = self.gsh.mark_headers(
                    start_row_index=start_index - 1,
                    end_row_index=start_index + self.PER_DAY_ROWS_COUNT - 1,
                    red_bg_color=r,
                    green_bg_color=g,
                    blue_bg_color=b,
                    bold=False,
                    sheetIndex=sheetIndex,
                    requests=requests)
            status, response = self.gsh.process_batch_requests(
                spreadsheetId=spreadsheet_id, requests=requests)
            response_object = {
                "processingTime": time.time() - total_time,
                "spreadsheetID": spreadsheet_id,
                "status": status,
                "Message": response
            }
        else:
            response_object = {"error_message": error_message}
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
