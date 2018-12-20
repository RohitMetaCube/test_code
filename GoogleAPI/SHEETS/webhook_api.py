import cherrypy
from log_utils import OneLineExceptionFormatter
import logging
import sys
import json
from collections import defaultdict
import requests
from time_sheet_api import TimeSheetAPI
import config
from db_utils import mongoDB
import time
import socket
import string
import random


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class Webhook(object):
    api_start_time = time.time()
    LOG_FORMAT_STRING = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    CLIENT_ID = "4ljR9SXowb_mHGOiqo45hA"
    CLIENT_SECRET = "7uhCPLOLDpBm87rokO8ORw"
    CLIENT_ID_PARAMETER = 'client_id'
    CODE_PARAMETER = 'code'
    ACCESS_TOKEN_PARAMETER = 'access_token'
    EMAIL_PARAMETER = "email"

    def __init__(self):
        self.intent_map = {
            'Welcome': self.hello,
            'Webhook Test': self.test_webhook,
            'Version': self.version,
            'Mark Entry': self.mark_entry,
            'Create Projects Sheets': self.create_project_sheet,
            'Add Work Log': self.add_work_log,
            'Get User Info': self.get_user_info,
            'User Login': self.access,
            'User Logout': self.user_logout
        }
        self.headers = {
            'content-type': 'application/json',
            'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
            "accept-language": "*"
        }
        self.mongo = mongoDB()
        self.wrs_access_token = None
        self.user_info = {}
        root.info("API Start Time= {}s".format(time.time() -
                                               Webhook.api_start_time))

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def access(self, **other_params):
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.headers['Connection'] = "close"

        try:
            params = cherrypy.request.params
            wrs_client_code = params[
                Webhook.
                CODE_PARAMETER] if Webhook.CODE_PARAMETER in params else None
            if wrs_client_code:
                r = requests.post(
                    "http://dev-accounts.agilestructure.in/sessions/get_access_token",
                    json={
                        Webhook.CODE_PARAMETER: wrs_client_code,
                        Webhook.CLIENT_ID_PARAMETER: Webhook.CLIENT_ID
                    })

                response_data = {}

                try:
                    self.wrs_access_token = r.json()[
                        Webhook.ACCESS_TOKEN_PARAMETER]

                    r = requests.get(
                        "http://dev-accounts.agilestructure.in/sessions/user_info.json",
                        headers={"Authorization": self.wrs_access_token},
                        params={})
                    r = r.json()
                    self.user_info.update(r)
                    response_data = {
                        "wrs_client_code": wrs_client_code,
                        "wrs_access_token": self.wrs_access_token,
                        "employee": r
                    }
                    response_data[
                        "fulfillmentText"] = "Welcome! How can I Help You."
                except Exception as e:
                    response_data = {
                        "fulfillmentText":
                        "Unable to fetch wrs access token for wrs client code {}".
                        format(wrs_client_code),
                        "error": str(e)
                    }
                finally:
                    return response_data
            else:
                return {
                    "fulfillmentText": "code parameter not returned by WRS"
                }
        except Exception as e:
            return {"fulfillmentText": "Unusual Exception Occur"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_user_info(self):
        data = self.user_info
        data['wrs_access_token'] = self.wrs_access_token
        return data

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def user_logout(self):
        # LogOut Call
        response = {}
        try:
            r = requests.post(
                "http://dev-accounts.agilestructure.in/sessions/logout.json",
                headers={"Authorization": self.wrs_access_token},
                json={Webhook.CLIENT_ID_PARAMETER: Webhook.CLIENT_ID})
            response.update(r.json())
            self.wrs_access_token = None
        except Exception as e:
            response.update({
                "error": "Unable to logout from WRS ::: {}".format(e)
            })
        return response

    def get_projects_of_an_employee(self, user_id):
        r = requests.get(
            "http://dev-services.agilestructure.in/api/v1/employees/projects.json",
            headers={"Authorization": self.wrs_access_token},
            params={"employee_ids": [user_id]})
        r = r.json()
        return r

    def get_manager_of_project(self, project_id):
        if self.user_info[config.WRS_EMAIL] == 'rohit.kumar@metacube.com':
            r = self.user_info[config.WRS_USER_UUID]
        else:
            r = requests.get(
                "http://dev-services.agilestructure.in/api/v1/groups/{}/manager.json".
                format(project_id),
                headers={"Authorization": self.wrs_access_token},
                params={"group_id": project_id})
            r = r.json()[config.WRS_UUID]
        return r

    def get_members_of_a_project(self, project_id):
        r = requests.get(
            "http://dev-services.agilestructure.in/api/v1/groups/{}/members.json".
            format(project_id),
            headers={"Authorization": self.wrs_access_token},
            params={"group_id": project_id})
        r = r.json()
        return r

    def hello(self, *argv, **kwargs):
        msg = "Hello from APIAI Webhook Integration."
        response = {}
        response["fulfillmentText"] = msg
        #response["fulfillmentMessages"] = [{'text': {'text': [msg]}}]
        return response

    def version(self, *argv, **kwargs):
        msg = "APIAI Webhook Integration. Version 2.0"
        response = {}
        response["fulfillmentText"] = msg
        #response["fulfillmentMessages"] = [{'text': {'text': [msg]}}]
        return response

    def test_webhook(self, *argv, **kwargs):
        msg = json.dumps({
            "speech": "Thank You for choosing python-webhook",
            "displayText": "I am in python-webhook",
            "source": "Timesheet ChatBot",
            "receivedContent": kwargs["params"] if "params" in kwargs else {}
        })
        response = {}
        response["fulfillmentText"] = msg
        #response["fulfillmentMessages"] = [{'text': {'text': [msg]}}]
        print response
        return response

    def sorry(self, *argv, **kwargs):
        response = {}
        response[
            "fulfillmentText"] = "Sorry We are unable to understand it !!! Please rephrase your query"
        if argv:
            response["fulfillmentText"] = argv[0]
        return response

    def get_matching_project(self, project_name):
        matching_project = None
        mJI = 0
        projects = self.get_projects_of_an_employee(self.user_info[
            config.WRS_USER_ID])
        logging.info(projects)
        for project in projects:
            if project[config.WRS_PROJECT_NAME] == project_name:
                matching_project = project
                break
            p1_tokens = project_name.split()
            p2_tokens = project[config.WRS_PROJECT_NAME].split()
            JI = len(set(p1_tokens).intersection(p2_tokens)) / len(
                set(p1_tokens).union(p2_tokens))
            if JI > 0.6 and JI > mJI:
                mJI = JI
                matching_project = project
        return matching_project

    def create_project_sheet(self, *args, **kwargs):
        month = kwargs['params'][config.MONTH] if config.MONTH in kwargs[
            'params'] else time.localtime()[1]
        year = kwargs['params'][config.YEAR] if config.YEAR in kwargs[
            'params'] else time.localtime()[0]
        project_name = None if TimeSheetAPI.PROJECT_NAME_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                TimeSheetAPI.PROJECT_NAME_PARAMETER]

        matching_project = self.get_matching_project(project_name)

        response = {}
        if matching_project:
            if self.get_manager_of_project(matching_project[
                    config.WRS_PROJECT_ID]) == self.user_info[
                        config.WRS_USER_UUID]:
                users = self.get_members_of_a_project(matching_project[
                    config.WRS_PROJECT_ID])
                if config.WRS_EMAIL in self.user_info and self.user_info[
                        config.WRS_EMAIL]:
                    data = {}
                    data[TimeSheetAPI.MONTH_PARAMETER] = month
                    data[TimeSheetAPI.YEAR_PARAMETER] = year
                    data[TimeSheetAPI.PROJECT_PARAMETER] = matching_project
                    data[TimeSheetAPI.USERS_PARAMETER] = users
                    data[TimeSheetAPI.MANAGER_INFO_PARAMETER] = self.user_info
                    response = requests.post(
                        "http://0.0.0.0:8081/timeSheet/create",
                        headers=self.headers,
                        json=data).json()

                    spreadsheet_id = response[
                        config.
                        SPREADSHEET_ID] if config.SPREADSHEET_ID in response else None
                    response[
                        "fulfillmentText"] = "Hey Buddy Say Thanks to me! Your spreadsheetID is {} for project {}".format(
                            spreadsheet_id, project_name)
                else:
                    response[
                        "fulfillmentText"] = "Sorry !!! We did not have your Email Address"
            else:
                response[
                    "fulfillmentText"] = "Sorry!!! You are not a Manager for project '{}'".format(
                        project_name)
        else:
            response[
                "fulfillmentText"] = "Your Project Name not found in our DB. If Possible please rephrase it."
        return response

    def mark_entry(self, *argv, **kwargs):
        data = kwargs['params']
        project_name = data[TimeSheetAPI.PROJECT_NAME_PARAMETER]
        matching_project = self.get_matching_project(project_name)
        if matching_project:
            iAmAdmin = False
            if self.get_manager_of_project(matching_project[
                    config.WRS_PROJECT_ID]) == self.user_info[
                        config.WRS_USER_UUID]:
                iAmAdmin = True
                data[TimeSheetAPI.MANAGER_INFO_PARAMETER] = self.user_info
            else:
                data[TimeSheetAPI.USER_INFO_PARAMETER] = self.user_info
            data[TimeSheetAPI.I_AM_MANAGER] = iAmAdmin
            data[TimeSheetAPI.PROJECT_PARAMETER] = matching_project
            response = requests.post(
                "http://0.0.0.0:8081/timeSheet/mark_entry",
                headers=self.headers,
                json=data).json()
            if "spreadsheetID" in response and response["status"]:
                response[
                    "fulfillmentText"] = "Congratulation!!! Your Entry marked in spreadsheetID: {}".format(
                        response["spreadsheetID"])
            elif "error_message" in response:
                response["fulfillmentText"] = response["error_message"]
            else:
                response[
                    "fulfillmentText"] = "Sorry I am unable to mark your entry please provide some more accurate details."
        else:
            response = {
                "fulfillmentText":
                "Project Name {} Not Matched with Employee {}".format(
                    project_name, self.user_info[config.WRS_NAME])
            }
        return response

    def add_work_log(self, *argv, **kwargs):
        data = kwargs['params']
        project_name = data[TimeSheetAPI.PROJECT_NAME_PARAMETER]
        matching_project = self.get_matching_project(project_name)
        if matching_project:
            iAmAdmin = False
            if self.get_manager_of_project(matching_project[
                    config.WRS_PROJECT_ID]) == self.user_info[
                        config.WRS_USER_UUID]:
                iAmAdmin = True
            data[TimeSheetAPI.I_AM_MANAGER] = iAmAdmin
            data[TimeSheetAPI.PROJECT_PARAMETER] = matching_project
            data[TimeSheetAPI.USER_INFO_PARAMETER] = self.user_info
            response = requests.post(
                "http://0.0.0.0:8081/timeSheet/add_work_log",
                headers=self.headers,
                json=data).json()
            if config.SPREADSHEET_ID in response:
                response[
                    "fulfillmentText"] = "Congratulation!!! Your work log added in spreadsheetID: {} for project: {}".format(
                        response[config.SPREADSHEET_ID],
                        response[config.WRS_PROJECT_NAME])
            elif "error_message" in response:
                response["fulfillmentText"] = response["error_message"]
            else:
                response[
                    "fulfillmentText"] = "Sorry I am unable to add your entry please provide some more accurate details."
        else:
            response = {
                "fulfillmentText":
                "Project Name {} Not Matched with Employee {}".format(
                    project_name, self.user_info[config.WRS_NAME])
            }
        return response

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def webhook(self):
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.headers['Connection'] = "close"

        params = defaultdict(dict)
        if cherrypy.request.method == "POST":
            params = cherrypy.request.json

        if "queryResult" in params and "intent" in params[
                "queryResult"] and "displayName" in params["queryResult"][
                    "intent"]:
            intent_name = params["queryResult"]["intent"]["displayName"]
            if intent_name in self.intent_map:
                params = params["queryResult"]["outputContexts"][0]
                response = self.intent_map[intent_name](
                    params=params['parameters'])
            else:
                response = self.sorry("Intent not specified in Webhook ::: {}".
                                      format(intent_name))
        else:
            response = self.sorry()

        return response

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def monitor(self):
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.headers['Connection'] = "close"
        cherrypy.response.status = 200
        thread_id = id_generator()
        response_json = {
            "containerId": socket.gethostname(),
            "threadId": thread_id
        }
        return response_json


if __name__ == "__main__":
    logging_handler = logging.StreamHandler(sys.stdout)
    log_format = OneLineExceptionFormatter(Webhook.LOG_FORMAT_STRING,
                                           Webhook.LOG_TIME_FORMAT)
    logging_handler.setFormatter(log_format)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(logging_handler)
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,  #5000,
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
        Webhook(),
        '/wrs',  #configurator.commons.JOB_NORMALIZATION_API_CONTEXT,
        config={'/': {}})
    cherrypy.engine.start()
    cherrypy.engine.block()
