import cherrypy
from log_utils import OneLineExceptionFormatter
from config import config
import logging
import sys
import json
from collections import defaultdict
from db_utils import mongoDB
import time
import socket
import string
import random
from intents.login import Login
from intents.logout import Logout
from intents.user_info import UserInfo
from intents.projects import Projects
from intents.create import CreateProject
from intents.remove import RemoveProject
from intents.add_log import AddWorkLog
from intents.mark_entry import MarkEntry


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class Webhook(object):
    api_start_time = time.time()
    LOG_FORMAT_STRING = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self):
        self.mongo = mongoDB()
        self.mongo.ensure_indexes(
            config.ACCESS_TOKENS,
            index_list=[
                config.DIALOG_FLOW_SESSION_ID, config.WRS_ACCESS_TOKEN
            ])
        self.user_login = Login(self.mongo)
        self.user_logout = Logout(self.mongo)
        self.user_info = UserInfo()
        self.user_projects = Projects(self.mongo)
        self.create_sheet = CreateProject(self.mongo, self.user_projects)
        self.remove_sheet = RemoveProject(self.mongo, self.user_projects)
        self.add_work_log = AddWorkLog(self.mongo, self.user_projects)
        self.mark_entry = MarkEntry(self.mongo, self.user_projects)

        self.intent_map = {
            'Welcome': self.hello,
            'Webhook Test': self.test_webhook,
            'Version': self.version,
            'User Login': self.user_login,
            'Get User Info': self.user_info,
            'Create Timesheet': self.create_sheet,
            'Remove Timesheet': self.remove_sheet,
            'Add Work Log': self.add_work_log,
            'Mark Entry': self.mark_entry,
            'User Logout': self.user_logout,
            'Project Names': self.user_projects
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
            msg = self.user_login.access(params)
        except Exception as e:
            msg = "Unusual Exception Occured ::: {}".format(e)
        return msg

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
                response["fulfillmentText"] = self.intent_map[
                    intent_name].apply(params=data)["fulfillmentText"]
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
            response["fulfillmentText"] = self.intent_map[params[
                "intent"]].apply(params=params)["fulfillmentText"]
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
