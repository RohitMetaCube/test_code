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


class Webhook:
    LOG_FORMAT_STRING = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
        self.intent_map = {
            'Welcome': self.hello,
            'Webhook Test': self.test_webhook,
            'Version': self.version,
            #'Create Timsheet': self.create_timesheet,
            'Mark Entry': self.mark_entry,
            'Create Projects Sheets': self.get_projects_sheets,
            'Add User': self.add_user,
            'Remove User': self.remove_user,
            'Add Work Log': self.add_work_log
        }
        self.headers = {
            'content-type': 'application/json',
            'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
            "accept-language": "*"
        }
        self.mongo = mongoDB()

    def hello(self, *argv, **kwargs):
        msg = "Hello from APIAI Webhook Integration."
        response = {}
        response["fulfillmentText"] = msg
        #response["fulfillmentMessages"] = [{'text': {'text': [msg]}}]
        return response

    def version(self, *argv, **kwargs):
        msg = "APIAI Webhook Integration. Version 1.0"
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

    def create_project_sheet(self,
                             month=None,
                             year=None,
                             project_name=None,
                             users=[]):
        data = {}
        data[TimeSheetAPI.MONTH_PARAMETER] = month
        data[TimeSheetAPI.YEAR_PARAMETER] = year
        data[TimeSheetAPI.PROJECT_NAME_PARAMETER] = project_name
        data[TimeSheetAPI.USERS_PARAMETER] = [{
            TimeSheetAPI.USERNAME_PARAMETER: user[config.NAME],
            TimeSheetAPI.USER_EMAIL_PARAMETER: user[config.EMAIL],
            TimeSheetAPI.USER_ID_PARAMETER: user[config.EMPLOYEE_ID]
        } for user in users]
        response = requests.post(
            "http://0.0.0.0:8080/timeSheet/create",
            headers=self.headers,
            json=data).json()

        spreadsheet_id = response[
            config.
            SPREADSHEET_ID] if config.SPREADSHEET_ID in response else None
        return spreadsheet_id

    def get_projects_sheets(self, *args, **kwargs):
        month = None if TimeSheetAPI.MONTH_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.MONTH_PARAMETER]
        year = None if TimeSheetAPI.YEAR_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.YEAR_PARAMETER]
        admin_email = None if TimeSheetAPI.ADMIN_EMAIL_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.ADMIN_EMAIL_PARAMETER]
        admin_id = None if "adminID" not in kwargs['params'] else kwargs[
            'params']["adminID"]
        projects = None if "projects" not in kwargs['params'] else kwargs[
            'params']['projects']

        spreadsheets = []
        if admin_email or admin_id:
            elem = None
            if admin_email and admin_id:
                elem = self.mongo.db[config.ADMIN_COLLECTION].find_one({
                    config.EMAIL: admin_email,
                    config.EMPLOYEE_ID: admin_id
                }, {config.PROJECTS_LIST: 1,
                    "_id": 1})
            if admin_email and not elem:
                elem = self.mongo.db[config.ADMIN_COLLECTION].find_one({
                    config.EMAIL: admin_email
                }, {config.PROJECTS_LIST: 1,
                    "_id": 1})
            if admin_id and not elem:
                elem = self.mongo.db[config.ADMIN_COLLECTION].find_one({
                    config.EMPLOYEE_ID: admin_id
                }, {config.PROJECTS_LIST: 1,
                    "_id": 1})

            if elem:
                if config.PROJECTS_LIST in elem:
                    updates = {}
                    for pindex, project in enumerate(elem[
                            config.PROJECTS_LIST]):
                        if not projects or project[
                                config.PROJECT_NAME] in projects:
                            new_entry = {
                                config.SPREADSHEET_ID: None,
                                config.PROJECT_NAME:
                                project[config.PROJECT_NAME]
                            }
                            if project[config.MONTH] == month and project[
                                    config.YEAR] == year:
                                new_entry[config.SPREADSHEET_ID] = project[
                                    config.SPREADSHEET_ID]
                                if not new_entry[config.SPREADSHEET_ID]:
                                    new_entry[
                                        config.
                                        SPREADSHEET_ID] = self.create_project_sheet(
                                            month=month,
                                            year=year,
                                            project_name=project[
                                                config.PROJECT_NAME],
                                            users=project[config.USERS_LIST])
                                    updates["{}.{}.{}".format(
                                        config.PROJECTS_LIST, pindex,
                                        config.SPREADSHEET_ID)] = new_entry[
                                            config.SPREADSHEET_ID]
                                    for uindex in range(
                                            len(project[config.USERS_LIST])):
                                        updates["{}.{}.{}.{}.{}".format(
                                            config.PROJECTS_LIST, pindex,
                                            config.USERS_LIST, uindex,
                                            config.USER_SHEET_INDEX)] = uindex
                            else:
                                new_entry[
                                    config.
                                    SPREADSHEET_ID] = self.create_project_sheet(
                                        month=month,
                                        year=year,
                                        project_name=project[
                                            config.PROJECT_NAME],
                                        users=project[config.USERS_LIST])
                                updates["{}.{}.{}".format(
                                    config.PROJECTS_LIST, pindex,
                                    config.SPREADSHEET_ID)] = new_entry[
                                        config.SPREADSHEET_ID]
                                if project[config.SPREADSHEET_ID] and (
                                        year > project[config.YEAR] or
                                        month > project[config.MONTH]):
                                    updates["{}.{}.{}.{}".format(
                                        config.PROJECTS_LIST, pindex, config.
                                        OLD_SHEETS, (month, year))] = project[
                                            config.SPREADSHEET_ID]
                                for uindex in range(
                                        len(project[config.USERS_LIST])):
                                    updates["{}.{}.{}.{}.{}".format(
                                        config.PROJECTS_LIST, pindex,
                                        config.USERS_LIST, uindex,
                                        config.USER_SHEET_INDEX)] = uindex
                            spreadsheets.append(new_entry)
                    if updates:
                        self.mongo.update_data(
                            config.ADMIN_COLLECTION,
                            query={"_id": elem["_id"]},
                            update_dict={"$set": updates},
                            upsert=False,
                            multi=False)
        response = {}
        if spreadsheets:
            response[
                "fulfillmentText"] = "Hey Buddy Say Thanks to me! Your spreadsheetIDs are {}".format(
                    "\n".join("projectName: {}, spreadsheetID: {}".format(
                        spreadsheet[config.PROJECT_NAME], spreadsheet[
                            config.SPREADSHEET_ID])
                              for spreadsheet in spreadsheets))
            self.mongo.append_new_users_in_userdb(
                admin_email=admin_email, admin_id=admin_id, projects=projects)
        else:
            response[
                "fulfillmentText"] = "Sorry I am unable to create Time-sheets please provide some more accurate details."
        return response

    def mark_entry(self, *argv, **kwargs):
        response = requests.post(
            "http://0.0.0.0:8080/timeSheet/mark_entry",
            headers=self.headers,
            json=kwargs['params']).json()
        if "spreadsheetID" in response and response["status"]:
            response[
                "fulfillmentText"] = "Congratulation!!! Your Entry marked in spreadsheetID: {}".format(
                    response["spreadsheetID"])
        elif "error_message" in response:
            response["fulfillmentText"] = response["error_message"]
        else:
            response[
                "fulfillmentText"] = "Sorry I am unable to mark your entry please provide some more accurate details."
        return response

    def add_user(self, *argv, **kwargs):
        admin_email = None if TimeSheetAPI.ADMIN_EMAIL_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.ADMIN_EMAIL_PARAMETER]
        admin_id = None if "adminID" not in kwargs['params'] else kwargs[
            'params']["adminID"]
        project_name = None if TimeSheetAPI.PROJECT_NAME_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                TimeSheetAPI.PROJECT_NAME_PARAMETER]
        user_name = None if TimeSheetAPI.USERNAME_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.USERNAME_PARAMETER]
        user_id = None if TimeSheetAPI.USER_ID_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.USER_ID_PARAMETER]
        user_email = None if TimeSheetAPI.USER_EMAIL_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.USER_EMAIL_PARAMETER]
        response = {}
        response["fulfillmentText"] = self.mongo.add_user(
            project_name, admin_email, admin_id, user_name, user_id,
            user_email)
        return response

    def remove_user(self, *argv, **kwargs):
        admin_email = None if TimeSheetAPI.ADMIN_EMAIL_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.ADMIN_EMAIL_PARAMETER]
        admin_id = None if "adminID" not in kwargs['params'] else kwargs[
            'params']["adminID"]
        project_name = None if TimeSheetAPI.PROJECT_NAME_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                TimeSheetAPI.PROJECT_NAME_PARAMETER]
        user_name = None if TimeSheetAPI.USERNAME_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.USERNAME_PARAMETER]
        user_id = None if TimeSheetAPI.USER_ID_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.USER_ID_PARAMETER]
        user_email = None if TimeSheetAPI.USER_EMAIL_PARAMETER not in kwargs[
            'params'] else kwargs['params'][TimeSheetAPI.USER_EMAIL_PARAMETER]
        response = {}
        response["fulfillmentText"] = self.mongo.remove_user(
            project_name, admin_email, admin_id, user_name, user_id,
            user_email)
        return response

    def add_work_log(self, *argv, **kwargs):
        response = requests.post(
            "http://0.0.0.0:8080/timeSheet/add_work_log",
            headers=self.headers,
            json=kwargs['params']).json()
        if config.SPREADSHEET_ID in response:
            response[
                "fulfillmentText"] = "Congratulation!!! Your work log added in spreadsheetID: {} for project: {}".format(
                    response[config.SPREADSHEET_ID],
                    response[config.PROJECT_NAME])
        elif "error_message" in response:
            response["fulfillmentText"] = response["error_message"]
        else:
            response[
                "fulfillmentText"] = "Sorry I am unable to add your entry please provide some more accurate details."
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
                response = self.intent_map[intent_name](
                    params=params['parameters'])
            else:
                response = self.sorry("Intent not specified in Webhook ::: {}".
                                      format(intent_name))
        else:
            response = self.sorry()

        return response


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
        'server.socket_port': 5000,
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
        '/',  #configurator.commons.JOB_NORMALIZATION_API_CONTEXT,
        config={'/': {}})
    cherrypy.engine.start()
    cherrypy.engine.block()
