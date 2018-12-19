# 192.168.16.114
import sys
import cherrypy
import time
import socket
import string
import random
import requests
import logging
from log_utils import OneLineExceptionFormatter


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class bot(object):
    api_start_time = time.time()
    CLIENT_ID = "4ljR9SXowb_mHGOiqo45hA"
    CLIENT_SECRET = "7uhCPLOLDpBm87rokO8ORw"
    CLIENT_ID_PARAMETER = 'client_id'
    CODE_PARAMETER = 'code'
    ACCESS_TOKEN_PARAMETER = 'access_token'
    EMAIL_PARAMETER = "email"

    def __init__(self):
        root.info("API Start Time= {}s".format(time.time() -
                                               bot.api_start_time))

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def access(self, **other_params):
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.headers['Connection'] = "close"

        try:
            params = cherrypy.request.params
            wrs_client_code = params[
                bot.CODE_PARAMETER] if bot.CODE_PARAMETER in params else None
            if wrs_client_code:
                r = requests.post(
                    "http://dev-accounts.agilestructure.in/sessions/get_access_token",
                    json={
                        bot.CODE_PARAMETER: wrs_client_code,
                        bot.CLIENT_ID_PARAMETER: bot.CLIENT_ID
                    })

                response_data = {}

                try:
                    wrs_access_token = r.json()[bot.ACCESS_TOKEN_PARAMETER]

                    r = requests.get(
                        "http://dev-accounts.agilestructure.in/sessions/user_info.json",
                        headers={"Authorization": wrs_access_token},
                        params={})
                    r = r.json()
                    r = requests.get(
                        "http://dev-services.agilestructure.in/api/v1/employees/{}.json".
                        format(r['user_uuid']),
                        headers={"Authorization": wrs_access_token},
                        params={"id": r["user_uuid"]})
                    r = r.json()
                    response_data = {
                        "wrs_client_code": wrs_client_code,
                        "wrs_access_token": wrs_access_token,
                        "employee": r
                    }
                except Exception as e:
                    response_data = {
                        "msg":
                        "Unable to fetch wrs access token for wrs client code {}".
                        format(wrs_client_code),
                        "error": str(e)
                    }
                finally:
                    # LogOut Call
                    try:
                        r = requests.post(
                            "http://dev-accounts.agilestructure.in/sessions/logout.json",
                            headers={"Authorization": wrs_access_token},
                            json={bot.CLIENT_ID_PARAMETER: bot.CLIENT_ID})
                        logging.info(r.json())
                    except Exception as e:
                        logging.info("Unable to logout from WRS ::: {}".format(
                            e))
                    return response_data
            else:
                return {"msg": "code parameter not returned by WRS"}
        except Exception as e:
            return {"msg": "Unusual Exception Occur"}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def get_wrs_data(self, **others):
        params = {}
        if cherrypy.request.method == "POST":
            params = cherrypy.request.json

        email = params[
            bot.EMAIL_PARAMETER] if bot.EMAIL_PARAMETER in params else ""

        if email:
            r = requests.get(
                "http://dev-accounts.agilestructure.in/sessions/new",
                params={
                    bot.EMAIL_PARAMETER: email,
                    bot.CLIENT_ID_PARAMETER: bot.CLIENT_ID,
                    "response_type": bot.CODE_PARAMETER
                },
                headers={
                    'User-Agent':
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
                    "accept-language": "*"
                })
            return r.json()
        else:
            return {
                "input_params": params,
                "msg": "Input Params did not have email parameter"
            }

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


class health_check:
    def __init__(self):
        self.init_time = int(time.time() * 1000)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def heartbeat(self, **params):
        current_time = int(time.time() * 1000)
        stats = {}
        response_json = {}
        response_json["upTime"] = self.init_time
        response_json["currentTime"] = current_time
        response_json["stats"] = stats
        return response_json


''' Initializing the web server '''
if __name__ == '__main__':
    LOG_FORMAT_STRING = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    logging_handler = logging.StreamHandler(sys.stdout)
    log_format = OneLineExceptionFormatter(LOG_FORMAT_STRING, LOG_TIME_FORMAT)
    logging_handler.setFormatter(log_format)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(logging_handler)
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'engine.timeout_monitor.on': False,
        'log.screen': False,
        'log.access_file': '',
        'log.error_log_propagate': False,
        'log.accrss_log.propagate': False,
        'log.error_file': ''
    })

    cherrypy.tree.mount(bot(), '/wrs', config={'/': {}})
    cherrypy.tree.mount(health_check(), '/', config={'/': {}})
    cherrypy.engine.start()
    cherrypy.engine.block()
