from pymongo import MongoClient, ASCENDING
import config


class mongoDB:
    def __init__(self,
                 host=config.MONGODB_HOST,
                 port=config.MONGODB_PORT,
                 db_name=config.MONGODB_NAME):
        self.db = MongoClient(host, port)[db_name]
        self.ensure_indexes(
            config.SHEETS_COLLECTION,
            index_list=[
                config.SPREADSHEET_ID,
                [config.EMAIL, config.MONTH, config.YEAR, config.PROJECT_NAME]
            ])
        self.ensure_indexes(
            config.LOGS_COLLECTION,
            index_list=[
                config.SPREADSHEET_ID, config.EMAIL, config.MANAGER_EMAIL
            ])

    def ensure_indexes(self, collection_name, index_list=[]):
        for index_name in index_list:
            if isinstance(index_name, (list, tuple, set)):
                self.db[collection_name].ensure_index(
                    [(sub_index_name, ASCENDING)
                     for sub_index_name in index_name])
            else:
                self.db[collection_name].ensure_index(index_name)

    def fetch_data(self,
                   collection_name,
                   fetch_type="cursor",
                   query={},
                   projection_list={},
                   limit_value=0,
                   page_number=1,
                   sort_type=0,
                   no_timeout=False):
        if limit_value and len(projection_list) and sort_type:
            collection_value = self.db[collection_name].find(
                query, projection_list,
                no_cursor_timeout=no_timeout).sort([("_id", sort_type)]).skip(
                    (page_number - 1) * limit_value).limit(limit_value)
        elif limit_value and sort_type:
            collection_value = self.db[collection_name].find(
                query,
                no_cursor_timeout=no_timeout).sort([("_id", sort_type)]).skip(
                    (page_number - 1) * limit_value).limit(limit_value)
        elif len(projection_list) and sort_type:
            collection_value = self.db[collection_name].find(
                query, projection_list,
                no_cursor_timeout=no_timeout).sort([("_id", sort_type)])
        elif sort_type:
            collection_value = self.db[collection_name].find(
                query, no_cursor_timeout=no_timeout).sort([("_id", sort_type)])
        elif len(projection_list) and limit_value:
            collection_value = self.db[collection_name].find(
                query, projection_list, no_cursor_timeout=no_timeout).skip(
                    (page_number - 1) * limit_value).limit(limit_value)
        elif len(projection_list):
            collection_value = self.db[collection_name].find(
                query, projection_list, no_cursor_timeout=no_timeout)
        elif limit_value:
            collection_value = self.db[collection_name].find(
                query, no_cursor_timeout=no_timeout).skip(
                    (page_number - 1) * limit_value).limit(limit_value)
        else:
            collection_value = self.db[collection_name].find(
                query, no_cursor_timeout=no_timeout)

        if fetch_type.lower() == "count":
            collection_value = collection_value.count()
        return collection_value

    def update_data(self,
                    collection_name,
                    query={},
                    update_dict={},
                    upsert=False,
                    multi=False):
        self.db[collection_name].update(
            query, update_dict, upsert=upsert, multi=multi)

    def fetch_spreadsheet_id_and_index(self,
                                       month=None,
                                       year=None,
                                       email=None,
                                       project=None):
        spreadsheet_id = None
        user_sheet_index = None
        user_name = None
        if month and year and email:
            elem = self.db[config.SHEETS_COLLECTION].find_one({
                config.EMAIL: email,
                config.YEAR: year,
                config.MONTH: month,
                config.PROJECT_NAME: project
            }, {config.SPREADSHEET_ID: 1,
                config.WRS_NAME: 1})
            if elem:
                spreadsheet_id = elem[config.SPREADSHEET_ID]
                user_name = elem[config.WRS_NAME]
                elem2 = self.db[config.LOGS_COLLECTION].find_one({
                    config.SPREADSHEET_ID: spreadsheet_id,
                    config.EMAIL: email
                }, {config.USER_SHEET_INDEX: 1})
                if elem2:
                    user_sheet_index = elem2[config.USER_SHEET_INDEX]
        return {
            config.SPREADSHEET_ID: spreadsheet_id,
            config.USER_SHEET_INDEX: user_sheet_index,
            config.WRS_NAME: user_name
        }

    def add_work_log(self,
                     spreadsheet_id,
                     email,
                     date,
                     task,
                     hours=0,
                     jira=None):
        self.update_data(
            config.LOGS_COLLECTION,
            query={config.SPREADSHEET_ID: spreadsheet_id,
                   config.EMAIL: email},
            update_dict={
                "$push": {
                    "{}.{}.{}".format(config.WORK_DETAILS, date,
                                      config.TASK_DETAILS): {
                                          config.WORKING_HOURS: hours,
                                          config.TASK_FIELD: task,
                                          config.JIRA_TICKET_NUMBER: jira,
                                          config.WORKING_ORDER_FIELD: None
                                      }
                }
            },
            upsert=False,
            multi=False)

    def add_leave(self, spreadsheet_id, email, date, ltype=None,
                  lpurpose=None):
        self.update_data(
            config.LOGS_COLLECTION,
            query={config.SPREADSHEET_ID: spreadsheet_id,
                   config.EMAIL: email},
            update_dict={
                "$push": {
                    "{}.{}".format(config.USER_LEAVES, date): {
                        config.LEAVE_PURPOSE: lpurpose,
                        config.LEAVE_TYPE: ltype,
                        config.LEAVE_APPROVED_STATUS: False
                    }
                }
            },
            upsert=False,
            multi=False)

    def add_wfh(self,
                spreadsheet_id,
                email,
                date,
                wfhtype=None,
                wfhpurpose=None):
        self.update_data(
            config.LOGS_COLLECTION,
            query={config.SPREADSHEET_ID: spreadsheet_id,
                   config.EMAIL: email},
            update_dict={
                "$push": {
                    "{}.{}".format(config.WORK_FROM_HOME, date): {
                        config.LEAVE_PURPOSE: wfhpurpose,
                        config.LEAVE_TYPE: wfhtype,
                        config.LEAVE_APPROVED_STATUS: False
                    }
                }
            },
            upsert=False,
            multi=False)

    def mark_special_working(self, spreadsheet_id, email, manager_email, date):
        self.update_data(
            config.LOGS_COLLECTION,
            query={
                config.SPREADSHEET_ID: spreadsheet_id,
                config.MANAGER_EMAIL: manager_email,
                config.EMAIL: email
            },
            update_dict={
                "$set": {
                    "{}.{}.{}".format(config.WORK_DETAILS, date,
                                      config.SPECIAL_WORKING_FLAG): True
                }
            },
            upsert=False,
            multi=False)

    def approve_leave(self, spreadsheet_id, email, manager_email, date):
        self.update_data(
            config.LOGS_COLLECTION,
            query={
                config.SPREADSHEET_ID: spreadsheet_id,
                config.MANAGER_EMAIL: manager_email,
                config.EMAIL: email
            },
            update_dict={
                "$set": {
                    "{}.{}.{}".format(config.USER_LEAVES, date,
                                      config.LEAVE_APPROVED_STATUS): True
                }
            },
            upsert=False,
            multi=False)

    def approve_wfh(self, spreadsheet_id, email, manager_email, date):
        self.update_data(
            config.LOGS_COLLECTION,
            query={
                config.SPREADSHEET_ID: spreadsheet_id,
                config.MANAGER_EMAIL: manager_email,
                config.EMAIL: email
            },
            update_dict={
                "$set": {
                    "{}.{}.{}".format(config.WORK_FROM_HOME, date,
                                      config.LEAVE_APPROVED_STATUS): True
                }
            },
            upsert=False,
            multi=False)

    def create_new_records(self, spreadsheet_id, manager, month, year, project,
                           users):
        self.db[config.SHEETS_COLLECTION].insert({
            config.SPREADSHEET_ID: spreadsheet_id,
            config.EMAIL: manager[config.WRS_EMAIL],
            config.USER_ID: manager[config.WRS_USER_ID],
            config.USER_UUID: manager[config.WRS_USER_UUID],
            config.YEAR: year,
            config.MONTH: month,
            config.PROJECT_NAME: project[config.WRS_PROJECT_NAME],
            config.WRS_PROJECT_ID: project[config.WRS_PROJECT_ID],
            config.WRS_PROJECT_UUID: project[config.WRS_PROJECT_UUID]
        })
        for i, user in enumerate(users):
            self.db[config.LOGS_COLLECTION].insert({
                config.SPREADSHEET_ID: spreadsheet_id,
                config.USER_SHEET_INDEX: i + 1,
                config.MANAGER_EMAIL: manager[config.WRS_EMAIL],
                config.EMAIL: user[config.WRS_EMAIL],
                config.USER_ID: user[config.WRS_USER_ID],
                config.USER_UUID: user[config.WRS_USER_UUID],
                config.WRS_EMPLOYEE_ID: user[config.WRS_EMPLOYEE_ID],
                config.WRS_NAME: user[config.WRS_NAME],
                config.WORK_DETAILS: {},
                config.WORK_FROM_HOME: {},
                config.USER_LEAVES: {}
            })
