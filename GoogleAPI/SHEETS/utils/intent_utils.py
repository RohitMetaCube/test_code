from db_utils import mongoDB
from intents.login import Login
from intents.logout import Logout
from intents.user_info import UserInfo
from intents.projects import Projects
from intents.create import CreateProject
from intents.remove import RemoveProject
from intents.add_log import AddWorkLog
from intents.mark_entry import MarkEntry
from intents.managers import Managers
from intents.work_summary import WorkSummary
from config import config


class Utils(object):
    def __init__(self):
        self.mongo = mongoDB()
        self.mongo.ensure_indexes(
            config.ACCESS_TOKENS,
            index_list=[
                config.DIALOG_FLOW_SESSION_ID, config.WRS_ACCESS_TOKEN
            ])
        self.user_login = Login(self.mongo)
        self.user_logout = Logout(self.mongo)
        self.user_info = UserInfo(self.mongo)
        self.user_projects = Projects(self.mongo)
        self.create_sheet = CreateProject(self.mongo, self.user_projects)
        self.remove_sheet = RemoveProject(self.mongo, self.user_projects)
        self.add_work_log = AddWorkLog(self.mongo, self.user_projects)
        self.mark_entry = MarkEntry(self.mongo, self.user_projects)
        self.managers = Managers(self.mongo)
        self.work_summary = WorkSummary(self.mongo, self.user_projects)

        self.intent_map = {
            'User Login': self.user_login,
            'Get User Info': self.user_info,
            'Create Timesheet': self.create_sheet,
            'Remove Timesheet': self.remove_sheet,
            'Add Work Log': self.add_work_log,
            'Mark Entry': self.mark_entry,
            'User Logout': self.user_logout,
            'Project Names': self.user_projects,
            'Managers': self.managers,
            'Work Summary': self.work_summary
        }
