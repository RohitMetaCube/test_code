from google_sheet_handler import GoogleSheetHandler
import math

WEEK_DAYS = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
    'Sunday'
]

BASE_DATE = (6, 11, 2017, WEEK_DAYS[0])

MONTHS = [
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December"
]


def compute_number_of_days(month, year):
    month -= 1
    number_of_days = 31 if (month % 7) % 2 == 0 else 30
    if MONTHS[month] == 'February':
        number_of_days = 28
        if year % 400 == 0 or (year % 100 != 0 and year % 4 == 0):
            number_of_days += 1
    return number_of_days


def compute_day(day, month, year):
    shifted_month = (month - 2) if month > 2 else (month + 10)
    last_2_digit_of_year = (year % 100) if month > 2 else (year % 100 - 1)
    first_2_digit_of_year = year / 100
    w = (day + int(math.floor(2.6 * shifted_month - 0.2)) +
         last_2_digit_of_year + int(math.floor(last_2_digit_of_year / 4.0)) +
         int(math.floor(first_2_digit_of_year / 4.0)) - 2 *
         first_2_digit_of_year)
    w %= 7
    if w < 0:
        w += 7
    day = (w + 6) % 7
    return day


def insert_header(employee_id=None,
                  employee_name=None,
                  sheetIndex=0,
                  sheetName=None):
    sheetName = "Sheet{}".format(sheetIndex +
                                 1) if not sheetName else sheetName
    data = []
    start_index = header_rows_count + 1
    end_index = number_of_days_in_week_1 * per_day_rows_count + header_rows_count
    for _ in range(4):
        d = "=SUM(F{}:F{})".format(start_index, end_index)
        data.append(d)
        start_index = end_index + 1
        end_index += 7 * per_day_rows_count
    end_index = start_index + number_of_days_in_week_5 * per_day_rows_count - 1
    d = "=SUM(F{}:F{})".format(start_index, end_index)
    data.append(d)

    data_list = [[
        "Name:  {}  -  {}".format(employee_id, employee_name)
        if (employee_id and employee_name) else "Employee Name", "", "", "",
        "", ""
    ], ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", ""], data,
                 ["", "", "Month", "=SUM(A3:E3)", "", ""],
                 ["Day", "Date", "Project", "Task", "Hrs spent", "Total Hrs"]]
    range_text = "{}!A{}:F{}".format(sheetName, 1, header_rows_count)
    gsh.update_data_in_sheet(
        spreadsheet_id=spreadsheet_id, range_=range_text, data_list=data_list)
    gsh.mark_headers(
        spreadsheetId=spreadsheet_id,
        start_row_index=0,
        end_row_index=1,
        red_bg_color=153,
        green_bg_color=204,
        blue_bg_color=255,
        sheetIndex=sheetIndex)
    gsh.mark_headers(
        spreadsheetId=spreadsheet_id,
        start_row_index=1,
        end_row_index=header_rows_count - 1,
        red_bg_color=238,
        green_bg_color=238,
        blue_bg_color=238,
        sheetIndex=sheetIndex)
    gsh.mark_headers(
        spreadsheetId=spreadsheet_id,
        start_row_index=header_rows_count - 1,
        end_row_index=header_rows_count,
        sheetIndex=sheetIndex)


def insert_rows(sheetIndex=0, sheetName=None, continue_day=None):
    sheetName = "Sheet{}".format(sheetIndex +
                                 1) if not sheetName else sheetName
    start_index = header_rows_count + 1
    end_index = start_index + per_day_rows_count * number_of_days - 1
    for day in range(1, number_of_days + 1):
        if continue_day and day<continue_day:
            start_index += per_day_rows_count
            continue
        day_index = compute_day(day, month, year)
        row = [#'{}'.format(WEEK_DAYS[compute_day(day, month, year)]),
               '=IF((INDIRECT(ADDRESS(ROW(),COLUMN()+1,4))<>0), TEXT(INDIRECT(ADDRESS(ROW(),COLUMN()+1,4)), "dddd"), "")',
               '{}/{}/{}'.format(month, day, year),
               "", "", "", "=SUM(E{}:E{})".format(start_index, start_index+per_day_rows_count-1)]
        data_list = [["", "", "", "", "", ""]
                     if i + 1 < per_day_rows_count else row
                     for i in range(per_day_rows_count)]
        range_text = "{}!A{}:F{}".format(sheetName, start_index,
                                         start_index + per_day_rows_count - 1)
        gsh.update_data_in_sheet(
            spreadsheet_id=spreadsheet_id,
            range_=range_text,
            data_list=data_list)
        gsh.merge_cells(
            spreadsheetId=spreadsheet_id,
            start_row_index=start_index - 1,
            end_row_index=start_index + per_day_rows_count - 1,
            start_col_index=0,
            end_col_index=2,
            sheetIndex=sheetIndex)
        gsh.merge_cells(
            spreadsheetId=spreadsheet_id,
            start_row_index=start_index - 1,
            end_row_index=start_index + per_day_rows_count - 1,
            start_col_index=5,
            end_col_index=6,
            sheetIndex=sheetIndex)
        if day_index in set([5, 6]):
            gsh.mark_headers(
                spreadsheetId=spreadsheet_id,
                start_row_index=start_index - 1,
                end_row_index=start_index + per_day_rows_count - 1,
                red_bg_color=204,
                green_bg_color=255,
                blue_bg_color=204,
                bold=False,
                sheetIndex=sheetIndex)
        start_index += per_day_rows_count

    data_list = [[
        "", "", "", "Total Hours", "",
        "=SUM(F{}:F{})".format(header_rows_count + 1, end_index)
    ]]
    range_text = "{}!A{}:F{}".format(sheetName, start_index, start_index)
    gsh.update_data_in_sheet(
        spreadsheet_id=spreadsheet_id, range_=range_text, data_list=data_list)
    gsh.mark_headers(
        spreadsheetId=spreadsheet_id,
        start_row_index=end_index,
        end_row_index=end_index + 1,
        sheetIndex=sheetIndex)


def add_weekly_sheet(sheetIndex=0, sheetName=None, users=[]):
    sheetName = "Sheet{}".format(sheetIndex +
                                 1) if not sheetName else sheetName

    data_list = []
    data_list.append([""] + users + ["Total"])
    data_list.append(["Week 1"] + ["='{}'!A3".format(user) for user in users] +
                     ["=sum(A2:{}2)".format(chr(ord("A") + len(users)))])
    data_list.append(["Week 2"] + ["='{}'!B3".format(user) for user in users] +
                     ["=sum(A3:{}3)".format(chr(ord("A") + len(users)))])
    data_list.append(["Week 3"] + ["='{}'!C3".format(user) for user in users] +
                     ["=sum(A4:{}4)".format(chr(ord("A") + len(users)))])
    data_list.append(["Week 4"] + ["='{}'!D3".format(user) for user in users] +
                     ["=sum(A5:{}5)".format(chr(ord("A") + len(users)))])
    data_list.append(["Week 5"] + ["='{}'!E3".format(user) for user in users] +
                     ["=sum(A6:{}6)".format(chr(ord("A") + len(users)))])
    data_list.append(["Sum"] + [
        "=sum({}2:{}6)".format(chr(ord("A") + i + 1), chr(ord("A") + i + 1))
        for i, user in enumerate(users)
    ] + [
        "=sum({}2:{}6)".format(
            chr(ord("A") + len(users) + 1), chr(ord("A") + len(users) + 1))
    ])

    range_text = "{}!A1:{}7".format(sheetName, chr(ord("A") + len(users) + 1))

    gsh.create_border(
        spreadsheetId=spreadsheet_id,
        sheetIndex=sheetIndex,
        end_row_index=7,
        end_col_index=len(users) + 2)

    gsh.update_data_in_sheet(
        spreadsheet_id=spreadsheet_id, range_=range_text, data_list=data_list)

    r, g, b = get_rgb_from_hex(color_hex="673AB7")
    gsh.mark_headers(
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

    gsh.mark_headers(
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


def add_sprint_hrs_sheet(sheetIndex=0, sheetName=None, users=[],
                         end_index=129):
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
        "=sum({}3:{}8)".format(chr(ord("A") + i + 1), chr(ord("A") + i + 1))
        for i, user in enumerate(users)
    ])

    range_text = "{}!A1:{}9".format(sheetName, chr(ord("A") + len(users)))

    gsh.create_border(
        spreadsheetId=spreadsheet_id,
        sheetIndex=sheetIndex,
        end_row_index=9,
        end_col_index=len(users) + 1)

    gsh.update_data_in_sheet(
        spreadsheet_id=spreadsheet_id, range_=range_text, data_list=data_list)

    r, g, b = get_rgb_from_hex(color_hex="B39DDB")
    gsh.mark_headers(
        spreadsheetId=spreadsheet_id,
        end_col_index=len(users) + 1,
        red_bg_color=r,
        green_bg_color=g,
        blue_bg_color=b,
        red_fg_color=255.0,
        green_fg_color=255.0,
        blue_fg_color=255.0,
        sheetIndex=sheetIndex)


def get_rgb_from_hex(color_hex="4A148C"):
    a = [
        int(x) if ("0" <= x <= "9") else (10 + ord(x) - ord("A"))
        for x in color_hex
    ]
    print a
    r = a[0] * 16 + a[1]
    g = a[2] * 16 + a[3]
    b = a[4] * 16 + a[5]
    return (r, g, b)


def add_projects_sheet(sheetIndex=0,
                       sheetName=None,
                       projects=[
                           "Client communication", "Documentation", "R&D",
                           "Team meeting", "Zippia"
                       ]):
    sheetName = "Sheet{}".format(sheetIndex +
                                 1) if not sheetName else sheetName

    data_list = []
    [data_list.append([project]) for project in projects]

    range_text = "{}!A1:A{}".format(sheetName, len(projects))

    gsh.update_data_in_sheet(
        spreadsheet_id=spreadsheet_id, range_=range_text, data_list=data_list)


if __name__ == "__main__":
    gsh = GoogleSheetHandler()
    month = 8
    year = 2018
    spreadsheet_id = None#'1dlRe5bw24tFmsloUHgNqUcfakFPLXSiPz3U6LLD34eg'
    sheets = [None, "Rohit", "Piyush Beli"]

    number_of_days = compute_number_of_days(month, year)
    day = compute_day(1, month, year)
    number_of_days_in_week_1 = (7 - day) if day < 5 else 7
    number_of_days_in_week_5 = number_of_days - 21 - number_of_days_in_week_1
    per_day_rows_count = 4
    header_rows_count = 5
    end_index = header_rows_count + 1 + per_day_rows_count * number_of_days

    if not spreadsheet_id:
        spreadsheet_id = gsh.create_google_sheet()["spreadsheetId"]

    for sheet_index, sheet_name in enumerate(sheets):
        if sheet_index:
            gsh.add_sheet(
                spreadsheetId=spreadsheet_id,
                sheetIndex=sheet_index,
                sheetName=sheet_name)
        else:
            gsh.create_border(
                spreadsheetId=spreadsheet_id,
                end_row_index=end_index,
                sheetIndex=sheet_index)
            insert_header(sheetIndex=sheet_index, sheetName=sheet_name)
            insert_rows(sheetIndex=sheet_index, sheetName=sheet_name,  continue_day=None)

    sheet_index += 1
    gsh.add_sheet(spreadsheetId=spreadsheet_id, sheetIndex=sheet_index, sheetName="Projects")
    add_projects_sheet(sheet_index, "Projects")

    sheet_index += 1
    gsh.add_sheet(spreadsheetId=spreadsheet_id, sheetIndex=sheet_index, sheetName="Weekly")
    add_weekly_sheet(sheet_index, "Weekly", sheets[1:])

    sheet_index += 1
    gsh.add_sheet(
        spreadsheetId=spreadsheet_id,
        sheetIndex=sheet_index,
        sheetName="Sprint - Hrs")
    add_sprint_hrs_sheet(
        sheet_index, "Sprint - Hrs", sheets[1:], end_index=end_index)

    # month_years = [(11,2017), (6,1987), (2, 2016), (2, 2000), (2, 1900), (7, 2017), (8, 2017), (1, 2017), (12, 2017)]
    # for month, year in month_years:
    #     print "Month: {}, Year: {}, Number of Days: {}".format(MONTHS[month-1], year, compute_number_of_days(month, year))
    #     
    #     
    # for i, month in enumerate(MONTHS):
    #     print "Month: {}, Number of Days: {}".format(month, compute_number_of_days(i+1, 2017))

    # dates = [(8, 6, 1987), (26, 10,1985), (2, 2, 1989), (7, 11, 2017), (1,1,2000)]
    # for day, month, year in dates:
    #     print "Date: {}-{}-{},  Day: {}".format(day, MONTHS[month-1], year, compute_day(day, month, year))

    # for month, year in [(2, 2016), (3, 2016)]:
    #     for day in range(1, compute_number_of_days(month, year)+1):
    #         print "Date: {}-{}-{}, Day: {}".format(day, MONTHS[month-1], year, compute_day(day, month, year))
    #     print 
