import requests
from config import config
from time_sheet_api import TimeSheetAPI
import time
from collections import defaultdict


class WorkSummary(object):
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo, project_obj):
        self.mongo = mongo
        self.project_obj = project_obj
        self.headers = config.REQUEST_HEADERS

    def type_converter(self, value, dtype):
        try:
            value = dtype(value)
        except:
            value = None
        return value

    def hours_data(self, summary_data):
        chart_data = [[tn, wh] for tn, wh in summary_data["work"].items()]
        for lt, ld in summary_data["leave"].items():
            chart_data.append([
                "Approved {} Leaves".format(lt),
                ld['Approved'] * config.DEFAULT_WORKING_HOURS_OF_A_DAY
            ])
            chart_data.append([
                "Applied {} Leaves".format(lt),
                ld['Applied'] * config.DEFAULT_WORKING_HOURS_OF_A_DAY
            ])
        for lt, ld in summary_data["wfh"].items():
            chart_data.append([
                "Approved {}".format(lt),
                ld['Approved'] * config.DEFAULT_WORKING_HOURS_OF_A_DAY
            ])
            chart_data.append([
                "Applied {}".format(lt),
                ld['Applied'] * config.DEFAULT_WORKING_HOURS_OF_A_DAY
            ])
        chart_data = [["{}".format(d[0]), d[1]] for d in chart_data]
        return chart_data

    def sprint_data(self, summary_data):
        chart_data = [[tn, wh] for tn, wh in summary_data["work"].items()]
        applied = 0
        approved = 0
        for ld in summary_data["leave"].values():
            applied += ld['Applied']
            approved += ld['Approved']
        chart_data.append([
            "Approved Leaves", approved * config.DEFAULT_WORKING_HOURS_OF_A_DAY
        ])
        chart_data.append([
            "Applied Leaves", applied * config.DEFAULT_WORKING_HOURS_OF_A_DAY
        ])
        applied = 0
        approved = 0
        for ld in summary_data["wfh"].values():
            applied += ld['Applied']
            approved += ld['Approved']
        chart_data.append(
            ["Approved WFH", approved * config.DEFAULT_WORKING_HOURS_OF_A_DAY])
        chart_data.append(
            ["Applied WFH", applied * config.DEFAULT_WORKING_HOURS_OF_A_DAY])
        chart_data = [["{}".format(d[0]), d[1]] for d in chart_data]
        return chart_data

    def day_data(self, detailed_data):
        task_type_count = defaultdict(int)
        for date in detailed_data["detailed"]:
            if "work" in detailed_data["detailed"][date]:
                for tt in detailed_data["detailed"][date]["work"]:
                    task_type_count[tt] += 1
        chart_data = [[k, v] for k, v in task_type_count.items()]
        chart_data.append([
            "Approved Leaves", detailed_data["leave"]['Approved']
            if detailed_data["leave"] else 0
        ])
        chart_data.append([
            "Applied Leaves", detailed_data["leave"]['Applied']
            if detailed_data["leave"] else 0
        ])
        chart_data.append([
            "Approved WFH", detailed_data["wfh"]['Approved']
            if detailed_data["wfh"] else 0
        ])
        chart_data.append([
            "Applied WFH", detailed_data["wfh"]['Applied']
            if detailed_data["wfh"] else 0
        ])
        chart_data = [["{}".format(d[0]), d[1]] for d in chart_data]
        return chart_data

    def week_data(self, detailed_data, week_stats):
        chart_data = defaultdict(float)
        for date, data in detailed_data['detailed'].items():
            date = int(date)
            if 0 < date < week_stats["totalDays"]:
                if date <= week_stats["numberOfDaysInFirstWeek"]:
                    chart_data['week 1'] += sum(data["work"].values(
                    )) if "work" in data and data["work"] else 0
                else:
                    date -= week_stats["numberOfDaysInFirstWeek"]
                    chart_data['week {}'.format((date % 7) + 2)] += sum(data[
                        "work"].values()) if "work" in data and data[
                            "work"] else 0
        chart_data = [["{}".format(k), v] for k, v in chart_data.items()]
        return chart_data

    def draw_pie_chart(self, summary_data, detailed_data, week_stats, project,
                       month, year):
        requests.post(
            "http://0.0.0.0:443/setChartData",
            json={
                "hours_data": self.hours_data(summary_data),
                "day_data": self.day_data(detailed_data),
                "week_data": self.week_data(detailed_data, week_stats),
                "sprint_data": self.sprint_data(summary_data),
                "project": project,
                "month": month,
                "year": year
            })

    def apply(self, *argv, **kwargs):
        session_id = None if WorkSummary.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                WorkSummary.DIALOGFLOW_SESSION_PARAMETER]
        elem = self.mongo.db[config.ACCESS_TOKENS].find_one({
            config.DIALOG_FLOW_SESSION_ID: session_id
        })
        response = {}
        if elem and config.WRS_ACCESS_TOKEN in elem and elem[
                config.WRS_ACCESS_TOKEN]:
            wrs_access_token = elem[config.WRS_ACCESS_TOKEN]
            user_info = elem[config.WRS_USER_INFO]

            data = kwargs['params']
            project_name = data[TimeSheetAPI.PROJECT_NAME_PARAMETER]
            matching_project = self.project_obj.get_matching_project(
                project_name, wrs_access_token, user_info)
            if matching_project:
                data[TimeSheetAPI.USER_INFO_PARAMETER] = user_info
                data[TimeSheetAPI.PROJECT_PARAMETER] = matching_project

                response = requests.post(
                    "http://0.0.0.0:8080/timeSheet/work_summary",
                    headers=self.headers,
                    json=data).json()
                if "summaryData" in response:
                    response["fulfillmentText"] = (
                        "Summary!!!</br>"
                        "<div>{}</div></br>"
                        "<div>{}</div></br>"
                        "<div>{}</div></br>"
                    ).format(
                        "<table border='1'><caption>Work Details</caption><tr><th>Task Name</th><th>Working Hours</th></tr>"
                        + "".join(
                            "<tr><td>{}</td><td>{}</td></tr>".format(task_name,
                                                                     work_hrs)
                            for task_name, work_hrs in response["summaryData"][
                                "work"].items()) + "</table>",
                        "<table border='1'><caption>Leave Details</caption><tr><th>Leave Type</th><th>Applied Count</th><th>Approved Count</th></tr>"
                        + "".join(
                            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".
                            format(leave_type, leave_details['Applied'],
                                   leave_details['Approved'])
                            for leave_type, leave_details in response[
                                "summaryData"]["leave"].items()) + "</table>",
                        "<table border='1'><caption>Wfh Details</caption><tr><th>WFH Type</th><th>Applied Count</th><th>Approved Count</th></tr>"
                        + "".join(
                            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".
                            format(wfh_type, wfh_details['Applied'],
                                   wfh_details['Approved'])
                            for wfh_type, wfh_details in response[
                                "summaryData"]["wfh"].items()) + "</table>")
                    month = self.type_converter(
                        data[TimeSheetAPI.MONTH_PARAMETER], int
                    ) if TimeSheetAPI.MONTH_PARAMETER in data else time.localtime(
                    )[1]
                    year = self.type_converter(
                        data[TimeSheetAPI.YEAR_PARAMETER], int
                    ) if TimeSheetAPI.YEAR_PARAMETER in data else time.localtime(
                    )[0]
                    self.draw_pie_chart(
                        response["summaryData"], response["detailedData"],
                        response["weekStats"],
                        matching_project[config.WRS_PROJECT_ID], month, year)
                    response["fulfillmentText"] += (
                        "<br><a target='_blank' rel='noopener noreferrer'"
                        "href='/showUserStats?project={}&month={}&year={}'>Pie Chart</a>"
                    ).format(matching_project[config.WRS_PROJECT_ID], month,
                             year)
                elif "error_message" in response:
                    response["fulfillmentText"] = response["error_message"]
                else:
                    response["fulfillmentText"] = (
                        "Sorry We are unable to fetch your project summary<br>"
                        "please provide some more accurate details.")
            else:
                response[
                    "fulfillmentText"] = "Project Name {} Not Matched with Employee {}".format(
                        project_name, user_info[config.WRS_USER_NAME]
                        if config.WRS_USER_NAME in user_info else
                        user_info[config.WRS_EMAIL])
        else:
            response["fulfillmentText"] = "Please Login First then try."
        return response
