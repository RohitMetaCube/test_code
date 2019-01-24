import requests
from config import config
from time_sheet_api import TimeSheetAPI
from BeautifulSoup import BeautifulSoup
import logging


class AddWorkLog(object):
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo, project_obj):
        self.mongo = mongo
        self.project_obj = project_obj
        self.headers = config.REQUEST_HEADERS

    def apply(self, *argv, **kwargs):
        session_id = None if AddWorkLog.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                AddWorkLog.DIALOGFLOW_SESSION_PARAMETER]
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
                required_params = [
                    TimeSheetAPI.PROJECT_NAME_PARAMETER,
                    TimeSheetAPI.WORK_DATE_PARAMETER,
                    TimeSheetAPI.WORKING_HOURS, TimeSheetAPI.WORK_DETAILS
                ]
                if any(rp not in data or not data[rp]
                       for rp in required_params):
                    session_tag = BeautifulSoup(
                        '<input type="hidden"  name="{}" value="{}" />'.format(
                            AddWorkLog.DIALOGFLOW_SESSION_PARAMETER,
                            session_id))
                    option_tag = BeautifulSoup(
                        "<option value='{}'>{}</option>".format(project_name,
                                                                project_name))
                    soup = BeautifulSoup(open("templates/work_log.html"))
                    for k, v in data.items():
                        try:
                            m = soup.find('', {'name': k})
                            m["value"] = v
                        except Exception as e:
                            logging.info("Parameter: {}, error: {}".format(k,
                                                                           e))

                    #soup = BeautifulSoup(str(soup))
                    m1 = soup.find('div', {'name': 'hidden_params'})
                    m2 = soup.find('select', {"name": 'taskType'})
                    # Add Session Id
                    m1.append(session_tag)
                    # Add Option
                    m2.append(option_tag)
                    response["fulfillmentText"] = str(soup)
                else:
                    iAmAdmin = False
                    if self.project_obj.get_manager_of_project(
                            matching_project[config.WRS_PROJECT_ID],
                            wrs_access_token)[config.WRS_UUID] == user_info[
                                config.WRS_USER_UUID]:
                        iAmAdmin = True
                    data[TimeSheetAPI.I_AM_MANAGER] = iAmAdmin
                    data[TimeSheetAPI.PROJECT_PARAMETER] = matching_project
                    data[TimeSheetAPI.USER_INFO_PARAMETER] = user_info
                    response = requests.post(
                        "http://0.0.0.0:8080/timeSheet/add_work_log",
                        headers=self.headers,
                        json=data).json()
                    if config.SPREADSHEET_ID in response:
                        response["fulfillmentText"] = (
                            "Congratulation!!!"
                            "</br>Your work log added</br>"
                            "for project: {}</br>"
                            "You can check it on</br>"
                            "<a target='_blank' rel='noopener noreferrer' href='https://docs.google.com/spreadsheets/d/{}'>this link</a>"
                        ).format(response[config.WRS_PROJECT_NAME],
                                 response[config.SPREADSHEET_ID])
                    elif "error_message" in response:
                        response["fulfillmentText"] = response["error_message"]
                    else:
                        response["fulfillmentText"] = (
                            "Sorry I am unable to add your entry</br>"
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
