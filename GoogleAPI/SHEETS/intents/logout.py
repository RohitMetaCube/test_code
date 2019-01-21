import requests
from config import config


class Logout(object):
    CLIENT_ID = config.CLIENT_ID
    CLIENT_ID_PARAMETER = config.CLIENT_ID_PARAMETER
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo):
        self.mongo = mongo

    def apply(self, *args, **kwargs):
        session_id = None if Logout.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                Logout.DIALOGFLOW_SESSION_PARAMETER]
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
                    json={Logout.CLIENT_ID_PARAMETER: Logout.CLIENT_ID})
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
