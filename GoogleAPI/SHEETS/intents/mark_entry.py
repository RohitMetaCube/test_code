import requests
from config import config
from time_sheet_api import TimeSheetAPI


class MarkEntry(object):
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo, project_obj):
        self.mongo = mongo
        self.project_obj = project_obj
        self.headers = config.REQUEST_HEADERS

    def apply(self, *argv, **kwargs):
        session_id = None if MarkEntry.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                MarkEntry.DIALOGFLOW_SESSION_PARAMETER]
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
                iAmAdmin = False
                if self.project_obj.get_manager_of_project(
                        matching_project[config.WRS_PROJECT_ID],
                        wrs_access_token,
                        user_info) == user_info[config.WRS_USER_UUID]:
                    iAmAdmin = True
                    data[TimeSheetAPI.MANAGER_INFO_PARAMETER] = user_info
                    data[TimeSheetAPI.USER_INFO_PARAMETER] = user_info
                else:
                    data[TimeSheetAPI.USER_INFO_PARAMETER] = user_info
                data[TimeSheetAPI.I_AM_MANAGER] = iAmAdmin
                data[TimeSheetAPI.PROJECT_PARAMETER] = matching_project

                response = requests.post(
                    "http://0.0.0.0:8080/timeSheet/mark_entry",
                    headers=self.headers,
                    json=data).json()
                if "spreadsheetID" in response and response["status"]:
                    response["fulfillmentText"] = (
                        "Congratulation!!!</br>Your Entry marked</br>You can check it on</br>"
                        "<a target='_blank' rel='noopener noreferrer'  href='https://docs.google.com/spreadsheets/d/{}'>this link</a>"
                    ).format(response["spreadsheetID"])
                elif "error_message" in response:
                    response["fulfillmentText"] = response["error_message"]
                else:
                    response["fulfillmentText"] = (
                        "Sorry I am unable to mark your entry"
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
