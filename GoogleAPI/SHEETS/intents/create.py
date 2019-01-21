import requests
from config import config
import time
from time_sheet_api import TimeSheetAPI


class CreateProject(object):
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo, project_obj):
        self.mongo = mongo
        self.project_obj = project_obj
        self.headers = config.REQUEST_HEADERS

    def apply(self, *args, **kwargs):
        month = kwargs['params'][config.MONTH] if config.MONTH in kwargs[
            'params'] else time.localtime()[1]
        year = kwargs['params'][config.YEAR] if config.YEAR in kwargs[
            'params'] else time.localtime()[0]
        project_name = None if TimeSheetAPI.PROJECT_NAME_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                TimeSheetAPI.PROJECT_NAME_PARAMETER]
        session_id = None if CreateProject.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                CreateProject.DIALOGFLOW_SESSION_PARAMETER]
        elem = self.mongo.db[config.ACCESS_TOKENS].find_one({
            config.DIALOG_FLOW_SESSION_ID: session_id
        })
        response = {}
        if elem and config.WRS_ACCESS_TOKEN in elem and elem[
                config.WRS_ACCESS_TOKEN]:
            wrs_access_token = elem[config.WRS_ACCESS_TOKEN]
            user_info = elem[config.WRS_USER_INFO]

            matching_project = self.project_obj.get_matching_project(
                project_name, wrs_access_token, user_info)

            if matching_project:
                if self.project_obj.get_manager_of_project(
                        matching_project[config.WRS_PROJECT_ID],
                        wrs_access_token,
                        user_info) == user_info[config.WRS_USER_UUID]:
                    users = self.project_obj.get_members_of_a_project(
                        matching_project[config.WRS_PROJECT_ID],
                        wrs_access_token)
                    if config.WRS_EMAIL in user_info and user_info[
                            config.WRS_EMAIL]:
                        data = {}
                        data[TimeSheetAPI.MONTH_PARAMETER] = month
                        data[TimeSheetAPI.YEAR_PARAMETER] = year
                        data[TimeSheetAPI.PROJECT_PARAMETER] = matching_project
                        data[TimeSheetAPI.USERS_PARAMETER] = users
                        data[TimeSheetAPI.MANAGER_INFO_PARAMETER] = user_info
                        response = requests.post(
                            "http://0.0.0.0:8080/timeSheet/create",
                            headers=self.headers,
                            json=data).json()

                        spreadsheet_id = response[
                            config.
                            SPREADSHEET_ID] if config.SPREADSHEET_ID in response else None
                        response["fulfillmentText"] = (
                            "We are creating your Timesheet</br>"
                            "of project {}</br>"
                            "<a target='_blank' rel='noopener noreferrer' href='https://docs.google.com/spreadsheets/d/{}'>at this link</a></br>"
                            "After Successful completion</br>"
                            "file will be shared with you</br>"
                            "on MetaCube Email").format(project_name,
                                                        spreadsheet_id)
                    else:
                        response[
                            "fulfillmentText"] = "Sorry !!! We did not have your Email Address"
                else:
                    response[
                        "fulfillmentText"] = "Sorry!!! You are not a Manager</br>for project '{}'".format(
                            project_name)
            else:
                response["fulfillmentText"] = (
                    "Your Project Name not found in our DB.</br>"
                    "If Possible please rephrase it.")
        else:
            response["fulfillmentText"] = "Please Login First then try."
        return response
