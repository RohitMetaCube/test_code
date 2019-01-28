import requests
from config import config
from time_sheet_api import TimeSheetAPI


class WorkSummary(object):
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo, project_obj):
        self.mongo = mongo
        self.project_obj = project_obj
        self.headers = config.REQUEST_HEADERS

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
                        "<table border='1'><caption>Work Details</caption><th><td>Task Name</td><td>Working Hours</td></th>"
                        + "".join(
                            "<tr><td>{}</td><td>{}</td></tr>".format(task_name,
                                                                     work_hrs)
                            for task_name, work_hrs in response["summaryData"][
                                "work"].items()) + "</table>",
                        "<table border='1'><caption>Leave Details</caption><th><td>Leave Type</td><td>Status</td><td>Count</td></th>"
                        + "".join(
                            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".
                            format(leave_type, leave_details['Applied'],
                                   leave_details['Approved'])
                            for leave_type, leave_details in response[
                                "summaryData"]["leave"].items()) + "</table>",
                        "<table border='1'><caption>Wfh Details</caption><th><td>WFH Type</td><td>Status</td><td>Count</td></th>"
                        + "".join(
                            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".
                            format(wfh_type, wfh_details['Applied'],
                                   wfh_details['Approved'])
                            for wfh_type, wfh_details in response[
                                "summaryData"]["wfh"].items()) + "</table>")
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
