import requests
from config import config


class Projects(object):
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo):
        self.mongo = mongo

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

    def apply(self, *args, **kwargs):
        session_id = None if Projects.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                Projects.DIALOGFLOW_SESSION_PARAMETER]
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

    def get_matching_project(self, project_name, wrs_access_token, user_info):
        project_name = project_name.lower()
        matching_project = None
        mJI = 0
        projects = self.get_projects_of_an_employee(
            user_info[config.WRS_USER_ID], wrs_access_token)
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
