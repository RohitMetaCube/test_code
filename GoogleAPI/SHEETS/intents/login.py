import requests
from config import config


class Login(object):
    CLIENT_ID = config.CLIENT_ID
    CLIENT_SECRET = config.CLIENT_SECRET
    CLIENT_ID_PARAMETER = config.CLIENT_ID_PARAMETER
    CODE_PARAMETER = config.CODE_PARAMETER
    ACCESS_TOKEN_PARAMETER = config.ACCESS_TOKEN_PARAMETER
    EMAIL_PARAMETER = config.EMAIL_PARAMETER
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo):
        self.mongo = mongo

    def access(self, params):
        response_data = {}
        try:
            wrs_client_code = params[
                Login.
                CODE_PARAMETER] if Login.CODE_PARAMETER in params else None
            if wrs_client_code:
                r = requests.post(
                    "http://dev-accounts.agilestructure.in/sessions/get_access_token",
                    json={
                        Login.CODE_PARAMETER: wrs_client_code,
                        Login.CLIENT_ID_PARAMETER: Login.CLIENT_ID
                    })

                try:
                    wrs_access_token = r.json()[Login.ACCESS_TOKEN_PARAMETER]

                    r = requests.get(
                        "http://dev-accounts.agilestructure.in/sessions/user_info.json",
                        headers={"Authorization": wrs_access_token},
                        params={})
                    r = r.json()
                    self.mongo.update_data(
                        config.ACCESS_TOKENS,
                        query={config.WRS_EMAIL: r[config.WRS_EMAIL]},
                        update_dict={
                            "$set": {
                                config.WRS_USER_INFO: r,
                                config.WRS_ACCESS_TOKEN: wrs_access_token
                            }
                        },
                        upsert=False,
                        multi=False)
                    response_data = {
                        "wrs_client_code": wrs_client_code,
                        "wrs_access_token": wrs_access_token,
                        "employee": r
                    }
                    response_data[
                        "fulfillmentText"] = "Welcome! You Are Registered Successfully."
                except Exception as e:
                    response_data = {
                        "fulfillmentText":
                        "Unable to fetch wrs access token for wrs client code {}".
                        format(wrs_client_code),
                        "error": str(e)
                    }
            else:
                response_data[
                    "fulfillmentText"] = "code parameter not returned by WRS"
        except Exception as e:
            response_data["fulfillmentText"] = "Unusual Exception Occur"
        msg = "<h2>{}</h2></br></br>".format(response_data["fulfillmentText"])
        if "employee" in response_data:
            msg += ("<style>"
                    "table, th, td {"
                    "border: 1px solid black;"
                    "border-collapse: collapse;"
                    "text-align: center;"
                    "}"
                    "table {"
                    "border-spacing: 15px;"
                    "}"
                    "table#t01 tr:nth-child(even) {"
                    "background-color: #eee;"
                    "}"
                    "table#t01 tr:nth-child(odd) {"
                    "background-color: #fff;"
                    "}"
                    "table#t01 th {"
                    "color: white;"
                    "background-color: black;"
                    "}"
                    "</style>")
            msg += ("<table style='width:100%' id=t01>"
                    "  <caption>User Details</caption>"
                    "  <tr>"
                    "    <th>Field</th>"
                    "    <th>Value</th>"
                    "  </tr>")
            for k, v in response_data["employee"].items():
                msg += ("<tr>"
                        "    <td>{}</td>"
                        "    <td>{}</td>"
                        "</tr>").format(k, v)
            msg += "</table>"
        return msg

    def apply(self, *args, **kwargs):
        session_id = None if Login.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][Login.DIALOGFLOW_SESSION_PARAMETER]
        email = None if Login.EMAIL_PARAMETER not in kwargs[
            'params'] else kwargs['params'][Login.EMAIL_PARAMETER]
        response = {}
        if email and session_id:
            self.mongo.update_data(
                config.ACCESS_TOKENS,
                query={config.WRS_EMAIL: email},
                update_dict={
                    "$set": {
                        config.DIALOG_FLOW_SESSION_ID: session_id
                    }
                },
                upsert=True,
                multi=False)
            text = (
                '<p>Click on this link for</br>'
                'Registration into WRS System</br>'
                'After successful register</br>'
                'you can use me for</br>'
                'your Timesheet management Tasks<br>'
                '<a target="_blank" rel="noopener noreferrer" href="http://dev-accounts.agilestructure.in/sessions/new?client_id={}&email={}&response_type=code">Please login here...</a><br>'
                '(<b>Note:</b> you will be taken to a new tab<br>and after completing the login<br>you can come back to the bot window.)</p>'
            ).format(Login.CLIENT_ID, email)
            response["fulfillmentText"] = text
        else:
            response[
                "fulfillmentText"] = "Unable to Logging</br>(Missing Parameters <email> or <session>)"
        return response
