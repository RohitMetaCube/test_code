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
                config.SPREADSHEET_ID, [
                    config.WRS_EMAIL, config.MONTH, config.YEAR,
                    config.WRS_PROJECT_NAME
                ]
            ])
        self.ensure_indexes(
            config.LOGS_COLLECTION,
            index_list=[
                config.SPREADSHEET_ID,
                config.WRS_EMAIL,
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
                                       project_name=None):
        spreadsheet_id = None
        user_sheet_index = None
        user_name = None
        if month and year and email:
            elem = self.db[config.SHEETS_COLLECTION].find_one({
                config.YEAR: year,
                config.MONTH: month,
                config.WRS_PROJECT_NAME: project_name
            }, {config.SPREADSHEET_ID: 1,
                config.WRS_NAME: 1})
            if elem:
                spreadsheet_id = elem[config.SPREADSHEET_ID]
                user_name = elem[config.WRS_NAME]
                elem2 = self.db[config.LOGS_COLLECTION].find_one({
                    config.SPREADSHEET_ID: spreadsheet_id,
                    config.WRS_EMAIL: email
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
                     task_type=None,
                     hours=0,
                     jira=None):
        self.update_data(
            config.LOGS_COLLECTION,
            query={
                config.SPREADSHEET_ID: spreadsheet_id,
                config.WRS_EMAIL: email
            },
            update_dict={
                "$push": {
                    "{}.{}.{}".format(config.WORK_DETAILS, date,
                                      config.TASK_DETAILS): {
                                          config.WORKING_HOURS: hours,
                                          config.TASK_FIELD: task,
                                          config.TASK_TYPE_FIELD: task_type,
                                          config.JIRA_TICKET_NUMBER: jira,
                                          config.WORKING_ORDER_FIELD: None
                                      }
                }
            },
            upsert=False,
            multi=False)

    def get_existing_work_logs(self, spreadsheet_id, email, date):
        work_details = []
        if date:
            date = str(date)
            work_logs_field = "{}.{}.{}".format(config.WORK_DETAILS, date,
                                                config.TASK_DETAILS)
            elem = self.fetch_data(
                config.LOGS_COLLECTION,
                'cursor',
                query={
                    config.SPREADSHEET_ID: spreadsheet_id,
                    config.WRS_EMAIL: email
                },
                projection_list={work_logs_field: 1})[0]
            if config.WORK_DETAILS in elem:
                if date in elem[config.WORK_DETAILS]:
                    if config.TASK_DETAILS in elem[config.WORK_DETAILS][date]:
                        work_details = elem[config.WORK_DETAILS][date][
                            config.TASK_DETAILS]
        return work_details

    def add_leave(self, spreadsheet_id, email, date, ltype=None,
                  lpurpose=None):
        self.update_data(
            config.LOGS_COLLECTION,
            query={
                config.SPREADSHEET_ID: spreadsheet_id,
                config.WRS_EMAIL: email
            },
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
            query={
                config.SPREADSHEET_ID: spreadsheet_id,
                config.WRS_EMAIL: email
            },
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

    def mark_special_working(self, spreadsheet_id, email, date):
        self.update_data(
            config.LOGS_COLLECTION,
            query={
                config.SPREADSHEET_ID: spreadsheet_id,
                config.WRS_EMAIL: email
            },
            update_dict={
                "$set": {
                    "{}.{}.{}".format(config.WORK_DETAILS, date,
                                      config.SPECIAL_WORKING_FLAG): True
                }
            },
            upsert=False,
            multi=False)

    def approve_leave(self, spreadsheet_id, email, date):
        self.update_data(
            config.LOGS_COLLECTION,
            query={
                config.SPREADSHEET_ID: spreadsheet_id,
                config.WRS_EMAIL: email
            },
            update_dict={
                "$set": {
                    "{}.{}.{}".format(config.USER_LEAVES, date,
                                      config.LEAVE_APPROVED_STATUS): True
                }
            },
            upsert=False,
            multi=False)

    def approve_wfh(self, spreadsheet_id, email, date):
        self.update_data(
            config.LOGS_COLLECTION,
            query={
                config.SPREADSHEET_ID: spreadsheet_id,
                config.WRS_EMAIL: email
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
            config.WRS_EMAIL: manager[config.WRS_EMAIL],
            config.WRS_ID: manager[config.WRS_USER_ID],
            config.WRS_UUID: manager[config.WRS_USER_UUID],
            config.WRS_EMPLOYEE_ID: manager[config.WRS_EMPLOYEE_ID]
            if config.WRS_EMPLOYEE_ID in manager else None,
            config.WRS_NAME: manager[config.WRS_USER_NAME]
            if config.WRS_USER_NAME in manager else None,
            config.YEAR: year,
            config.MONTH: month,
            config.WRS_PROJECT_NAME: project[config.WRS_PROJECT_NAME],
            config.WRS_PROJECT_ID: project[config.WRS_PROJECT_ID],
            config.WRS_PROJECT_UUID: project[config.WRS_PROJECT_UUID]
        })
        for i, user in enumerate(users):
            self.db[config.LOGS_COLLECTION].insert({
                config.SPREADSHEET_ID: spreadsheet_id,
                config.USER_SHEET_INDEX: i + 1,
                config.WRS_EMAIL: user[config.WRS_EMAIL],
                config.WRS_ID: user[config.WRS_ID],
                config.WRS_UUID: user[config.WRS_UUID],
                config.WRS_EMPLOYEE_ID: user[config.WRS_EMPLOYEE_ID]
                if config.WRS_EMPLOYEE_ID in user else None,
                config.WRS_NAME: user[config.WRS_NAME]
                if config.WRS_NAME in user else None,
                config.WORK_DETAILS: {},
                config.WORK_FROM_HOME: {},
                config.USER_LEAVES: {}
            })

    def remove_spreadsheet(self, month=None, year=None, project_name=None):
        spreadsheet_id = None
        if month and year:
            elem = self.db[config.SHEETS_COLLECTION].find_one({
                config.YEAR: year,
                config.MONTH: month,
                config.WRS_PROJECT_NAME: project_name
            }, {config.SPREADSHEET_ID: 1})
            if elem:
                spreadsheet_id = elem[config.SPREADSHEET_ID]
                self.db[config.LOGS_COLLECTION].remove({
                    config.SPREADSHEET_ID: spreadsheet_id
                })
                self.db[config.SHEETS_COLLECTION].remove({
                    config.SPREADSHEET_ID: spreadsheet_id
                })
        return spreadsheet_id
