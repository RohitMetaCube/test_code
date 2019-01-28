import requests
from config import config
from time_sheet_api import TimeSheetAPI
from BeautifulSoup import BeautifulSoup


class WorkSummary(object):
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo, project_obj):
        self.mongo = mongo
        self.project_obj = project_obj
        self.headers = config.REQUEST_HEADERS

    def draw_pie_chart(self, data):
        soup = BeautifulSoup(open("templates/pie_chart.html"))
        try:
            m = soup.find('', {'id': "data"})
            m["value"] = data
        except Exception as e:
            soup = "Error in pie chart data adding: {}".format(e)
        return str(soup)

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
                    data = response["summaryData"]["work"].items()
                    for lt, ld in response["summaryData"]["leave"].items():
                        data.append(
                            ["Approved {} Leaves".format(lt), ld['Approved']])
                        data.append(
                            ["Applied {} Leaves".format(lt), ld['Applied']])
                    for lt, ld in response["summaryData"]["wfh"].items():
                        data.append(
                            ["Approved {} WFH".format(lt), ld['Approved']])
                        data.append(
                            ["Applied {} WFH".format(lt), ld['Applied']])
                    response["fulfillmentText"] = self.draw_pie_chart(data)

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
