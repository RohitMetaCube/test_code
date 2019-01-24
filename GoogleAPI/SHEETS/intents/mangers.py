import requests
from config import config


class Managers(object):
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo):
        self.mongo = mongo

    def get_primary_manager_of_an_employee(self, user_id, wrs_access_token):
        r = requests.get(
            "http://dev-services.agilestructure.in/api/v1/employees/{}/manager.json".
            format(user_id),
            headers={"Authorization": wrs_access_token},
            params={"employee_id": [user_id]})
        r = r.json()
        return r

    def primary_manager(self, user_id, wrs_access_token):
        primary_manager = self.get_primary_manager_of_an_employee(
            user_id, wrs_access_token)
        return (
            "<div><div><img src='{}' alt='Smiley face' height='42' width='42'><div><div>Name: {}<br>Email: {}<br>EmployeeId: {}</div></div>"
        ).format(primary_manager[config.WRS_IMAGE],
                 primary_manager[config.WRS_NAME],
                 primary_manager[config.WRS_EMAIL],
                 primary_manager[config.WRS_ID])

    def project_manage(self, project_id, user_id, wrs_access_token):
        return "For now Rohit is the only project manger"

    def apply(self, *args, **kwargs):
        session_id = None if Managers.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                Managers.DIALOGFLOW_SESSION_PARAMETER]
        project_id = None
        elem = self.mongo.db[config.ACCESS_TOKENS].find_one({
            config.DIALOG_FLOW_SESSION_ID: session_id
        })
        response = {}
        if elem and config.WRS_ACCESS_TOKEN in elem and elem[
                config.WRS_ACCESS_TOKEN]:
            wrs_access_token = elem[config.WRS_ACCESS_TOKEN]
            user_info = elem[config.WRS_USER_INFO]
            if not project_id:
                response["fulfillmentText"] = self.primary_manager(
                    user_info[config.WRS_USER_ID], wrs_access_token)
            else:
                response["fulfillmentText"] = self.project_manage(
                    project_id, user_info[config.WRS_USER_ID],
                    wrs_access_token)
        else:
            response["fulfillmentText"] = "Please Login First then try."
        return response
