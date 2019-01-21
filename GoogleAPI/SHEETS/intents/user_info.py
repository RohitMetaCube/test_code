from config import config


class UserInfo(object):
    DIALOGFLOW_SESSION_PARAMETER = config.DIALOGFLOW_SESSION_PARAMETER

    def __init__(self, mongo):
        self.mongo = mongo

    def apply(self, *args, **kwargs):
        session_id = None if UserInfo.DIALOGFLOW_SESSION_PARAMETER not in kwargs[
            'params'] else kwargs['params'][
                UserInfo.DIALOGFLOW_SESSION_PARAMETER]
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
