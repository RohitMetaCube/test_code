import cherrypy
from log_utils import OneLineExceptionFormatter
from config import config
import logging
import sys
import json
from collections import defaultdict
import requests
from time_sheet_api import TimeSheetAPI
from db_utils import mongoDB
import time
import socket
import string
import random
from BeautifulSoup import BeautifulSoup
from intents.login import Login


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
    DIALOGFLOW_SESSION_PARAMETER = "session"

    def __init__(self):
        self.mongo = mongoDB()
        self.mongo.ensure_indexes(
            config.ACCESS_TOKENS,
            index_list=[
                config.DIALOG_FLOW_SESSION_ID, config.WRS_ACCESS_TOKEN
            ])
        self.login_obj = Login(self.mongo)
        self.intent_map = {
            'Welcome': self.hello,
            'Webhook Test': self.test_webhook,
            'Version': self.version,
            'User Login': self.login_obj.user_login,
            'Get User Info': self.get_user_info,
            'Create Timesheet': self.create_project_sheet,
            'Remove Timesheet': self.remove_project_sheet,
            'Add Work Log': self.add_work_log,
            'Mark Entry': self.mark_entry,
            'User Logout': self.user_logout,
            'Project Names': self.get_project_names
        }
        self.headers = {
            'content-type': 'application/json',
            'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
            "accept-language": "*"
        }
        root.info("API Start Time= {}s".format(time.time() -
                                               Webhook.api_start_time))

    @cherrypy.expose
    def access(self, **other_params):
        cherrypy.response.headers['Content-Type'] = "text/html"
        cherrypy.response.headers['Connection'] = "close"

        try:
            params = cherrypy.request.params
            msg = self.login_obj.access(params)
        except Exception as e:
            msg = "Unusual Exception Occured ::: {}".format(e)
        return msg

    def get_user_info(self, *args, **kwargs):
        session_id = None if Webhook.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                Webhook.DIALOGFLOW_SESSION_PARAMETER]
        response = {}
        elem = self.mongo.db[config.ACCESS_TOKENS].find_one({
            config.DIALOG_FLOW_SESSION_ID: session_id
        })
        if elem and config.WRS_ACCESS_TOKEN in elem and elem[
                config.WRS_ACCESS_TOKEN]:
            wrs_access_token = elem[
                config.
                WRS_ACCESS_TOKEN] if config.WRS_ACCESS_TOKEN in elem else None
            user_info = elem[
                config.WRS_USER_INFO] if config.WRS_USER_INFO in elem else {}
            response["fulfillmentText"] = (
                "<ul><li>name: {}</li>"
                "<li>id: {}</li>"
                "<li>uuid: {}</li>"
                "<li>email: {}</li>"
                "<li>access_token: {}</li></ul>").format(
                    user_info[config.WRS_USER_NAME]
                    if config.WRS_USER_NAME in user_info else None,
                    user_info[config.WRS_USER_ID]
                    if config.WRS_USER_ID in user_info else None,
                    user_info[config.WRS_USER_UUID]
                    if config.WRS_USER_UUID in user_info else None,
                    user_info[config.WRS_EMAIL] if
                    config.WRS_EMAIL in user_info else None, wrs_access_token)
        else:
            response["fulfillmentText"] = "Please Login First then try."
        return response

    def user_logout(self, *args, **kwargs):
        session_id = None if Webhook.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                Webhook.DIALOGFLOW_SESSION_PARAMETER]
        elem = self.mongo.db[config.ACCESS_TOKENS].find_one({
            config.DIALOG_FLOW_SESSION_ID: session_id
        }, {config.WRS_ACCESS_TOKEN: 1})
        wrs_access_token = elem[
            config.
            WRS_ACCESS_TOKEN] if elem and config.WRS_ACCESS_TOKEN in elem else None

        response = {}
        if wrs_access_token:
            # Remove Session Details from DB
            self.mongo.db[config.ACCESS_TOKENS].remove({
                config.WRS_ACCESS_TOKEN: wrs_access_token
            })

            # LogOut Call
            try:
                r = requests.post(
                    "http://dev-accounts.agilestructure.in/sessions/logout.json",
                    headers={"Authorization": wrs_access_token},
                    json={Webhook.CLIENT_ID_PARAMETER: Webhook.CLIENT_ID})
                r = r.json()
                response["fulfillmentText"] = r[
                    "msg"] if "msg" in r else "You are being logging out ....."
            except Exception as e:
                response.update({
                    "fulfillmentText":
                    "Unable to logout from WRS ::: {}".format(e)
                })
        else:
            response["fulfillmentText"] = "You are already logged out."
            self.mongo.db[config.ACCESS_TOKENS].remove({
                config.DIALOG_FLOW_SESSION_ID: session_id
            })
        return response

    def get_project_names(self, *args, **kwargs):
        session_id = None if Webhook.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                Webhook.DIALOGFLOW_SESSION_PARAMETER]
        elem = self.mongo.db[config.ACCESS_TOKENS].find_one({
            config.DIALOG_FLOW_SESSION_ID: session_id
        })
        response = {}
        if elem and config.WRS_ACCESS_TOKEN in elem and elem[
                config.WRS_ACCESS_TOKEN]:
            wrs_access_token = elem[config.WRS_ACCESS_TOKEN]
            user_info = elem[config.WRS_USER_INFO]
            projects = self.get_projects_of_an_employee(
                user_info[config.WRS_USER_ID], wrs_access_token)
            response["fulfillmentText"] = "<ul><li>{}</li></ul>".format(
                "</li><li>".join(project[config.WRS_PROJECT_NAME]
                                 for project in projects))
        else:
            response["fulfillmentText"] = "Please Login First then try."
        return response

    def get_projects_of_an_employee(self, user_id, wrs_access_token):
        r = requests.get(
            "http://dev-services.agilestructure.in/api/v1/employees/projects.json",
            headers={"Authorization": wrs_access_token},
            params={"employee_ids": [user_id]})
        r = r.json()
        return r

    def get_manager_of_project(self, project_id, wrs_access_token, user_info):
        r = requests.get(
            "http://dev-services.agilestructure.in/api/v1/groups/{}/manager.json".
            format(project_id),
            headers={"Authorization": wrs_access_token},
            params={"group_id": project_id})
        r = r.json()[config.WRS_UUID]
        return r

    def get_members_of_a_project(self, project_id, wrs_access_token):
        field_map = {
            config.WRS_EMAIL: config.WRS_EMPLOYEE_EMAIL,
            config.WRS_ID: config.WRS_EMPLOYEE_USER_ID,
            config.WRS_UUID: config.WRS_EMPLOYEE_USER_UUID,
            config.WRS_NAME: config.WRS_EMPLOYEE_USER_NAME
        }
        r = requests.get(
            "http://dev-services.agilestructure.in/api/v1/groups/{}/members.json".
            format(project_id),
            headers={"Authorization": wrs_access_token},
            params={"group_id": project_id})
        r = r.json()
        r = [{k: user[v] for k, v in field_map.items()} for user in r]
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

    def get_matching_project(self, project_name, wrs_access_token, user_info):
        project_name = project_name.lower()
        matching_project = None
        mJI = 0
        projects = self.get_projects_of_an_employee(
            user_info[config.WRS_USER_ID], wrs_access_token)
        logging.info(projects)
        for project in projects:
            if project[config.WRS_PROJECT_NAME].lower() == project_name:
                matching_project = project
                break
            p1_tokens = project_name.split()
            p2_tokens = project[config.WRS_PROJECT_NAME].lower().split()
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
        session_id = None if Webhook.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                Webhook.DIALOGFLOW_SESSION_PARAMETER]
        elem = self.mongo.db[config.ACCESS_TOKENS].find_one({
            config.DIALOG_FLOW_SESSION_ID: session_id
        })
        response = {}
        if elem and config.WRS_ACCESS_TOKEN in elem and elem[
                config.WRS_ACCESS_TOKEN]:
            wrs_access_token = elem[config.WRS_ACCESS_TOKEN]
            user_info = elem[config.WRS_USER_INFO]

            matching_project = self.get_matching_project(
                project_name, wrs_access_token, user_info)

            if matching_project:
                if self.get_manager_of_project(
                        matching_project[config.WRS_PROJECT_ID],
                        wrs_access_token,
                        user_info) == user_info[config.WRS_USER_UUID]:
                    users = self.get_members_of_a_project(
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

    def remove_project_sheet(self, *args, **kwargs):
        month = kwargs['params'][config.MONTH] if config.MONTH in kwargs[
            'params'] else time.localtime()[1]
        year = kwargs['params'][config.YEAR] if config.YEAR in kwargs[
            'params'] else time.localtime()[0]
        project_name = None if TimeSheetAPI.PROJECT_NAME_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                TimeSheetAPI.PROJECT_NAME_PARAMETER]
        session_id = None if Webhook.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                Webhook.DIALOGFLOW_SESSION_PARAMETER]
        elem = self.mongo.db[config.ACCESS_TOKENS].find_one({
            config.DIALOG_FLOW_SESSION_ID: session_id
        })
        response = {}
        if elem and config.WRS_ACCESS_TOKEN in elem and elem[
                config.WRS_ACCESS_TOKEN]:
            wrs_access_token = elem[config.WRS_ACCESS_TOKEN]
            user_info = elem[config.WRS_USER_INFO]

            matching_project = self.get_matching_project(
                project_name, wrs_access_token, user_info)

            if matching_project:
                if self.get_manager_of_project(
                        matching_project[config.WRS_PROJECT_ID],
                        wrs_access_token,
                        user_info) == user_info[config.WRS_USER_UUID]:
                    if config.WRS_EMAIL in user_info and user_info[
                            config.WRS_EMAIL]:
                        data = {}
                        data[TimeSheetAPI.MONTH_PARAMETER] = month
                        data[TimeSheetAPI.YEAR_PARAMETER] = year
                        data[TimeSheetAPI.PROJECT_PARAMETER] = matching_project
                        response = requests.post(
                            "http://0.0.0.0:8080/timeSheet/remove",
                            headers=self.headers,
                            json=data).json()

                        spreadsheet_id = response[
                            config.
                            SPREADSHEET_ID] if config.SPREADSHEET_ID in response else None
                        response[
                            "fulfillmentText"] = "Successfully Removed {}'s Time-sheet from our system.".format(
                                spreadsheet_id, project_name)
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

    def mark_entry(self, *argv, **kwargs):
        session_id = None if Webhook.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                Webhook.DIALOGFLOW_SESSION_PARAMETER]
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
            matching_project = self.get_matching_project(
                project_name, wrs_access_token, user_info)
            if matching_project:
                iAmAdmin = False
                if self.get_manager_of_project(
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

    def add_work_log(self, *argv, **kwargs):
        session_id = None if Webhook.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                Webhook.DIALOGFLOW_SESSION_PARAMETER]
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
            matching_project = self.get_matching_project(
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
                            Webhook.DIALOGFLOW_SESSION_PARAMETER, session_id))
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
                    if self.get_manager_of_project(
                            matching_project[config.WRS_PROJECT_ID],
                            wrs_access_token,
                            user_info) == user_info[config.WRS_USER_UUID]:
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

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
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
                session_id = params[Webhook.DIALOGFLOW_SESSION_PARAMETER]
                if "outputContexts" in params[
                        "queryResult"] and 'parameters' in params[
                            "queryResult"]["outputContexts"][0]:
                    params = params["queryResult"]["outputContexts"][0]
                    data = params['parameters']
                elif "parameters" in params["queryResult"]:
                    data = params["queryResult"]["parameters"]
                else:
                    data = {}
                data.update({Webhook.DIALOGFLOW_SESSION_PARAMETER: session_id})
                response = {}
                response["fulfillmentText"] = self.intent_map[intent_name](
                    params=data)["fulfillmentText"]
            else:
                response = self.sorry("Intent not specified in Webhook ::: {}".
                                      format(intent_name))
        else:
            response = self.sorry()

        return response

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def form_webhook(self, *args, **kwargs):
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.headers['Connection'] = "close"

        params = cherrypy.request.params

        response = {}
        if "source" in params and "intent" in params:
            response["fulfillmentText"] = self.intent_map[params["intent"]](
                params=params)["fulfillmentText"]
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


class botUI(object):
    def __init__(self):
        ''

    @cherrypy.expose
    def home(self):
        return open("UI/index.html")

    @cherrypy.expose
    def mbot(self):
        return open("UI/mbot.html")

    @cherrypy.expose
    def agentDomJs(self):
        return open("UI/jscripts/agentDemo.bundle.min.js")


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
        'server.socket_port': 443,  #5000,
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
    cherrypy.tree.mount(
        botUI(),
        '/',  #configurator.commons.JOB_NORMALIZATION_API_CONTEXT,
        config={'/': {}})
    cherrypy.engine.start()
    cherrypy.engine.block()
