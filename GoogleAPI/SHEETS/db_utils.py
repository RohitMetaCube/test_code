from pymongo import MongoClient, ASCENDING
import config


class mongoDB:
    def __init__(self,
                 host=config.MONGODB_HOST,
                 port=config.MONGODB_PORT,
                 db_name=config.MONGODB_NAME):
        self.db = MongoClient(host, port)[db_name]
        self.ensure_indexes(
            config.USER_COLLECTION,
            index_list=[
                config.SPREADSHEET_ID,
                [config.ADMIN_EMAIL, config.MONTH, config.YEAR]
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
            cursor = self.db[config.USER_COLLECTION].find({
                config.EMAIL: email,
                config.YEAR: year,
                config.MONTH: month
            }, {
                config.SPREADSHEET_ID: 1,
                config.USER_SHEET_INDEX: 1,
                config.PROJECT_NAME: 1,
                config.NAME: 1
            })
            if cursor.count() == 1:
                elem = cursor[0]
                if config.SPREADSHEET_ID in elem:
                    spreadsheet_id = elem[config.SPREADSHEET_ID]
                    user_sheet_index = elem[config.USER_SHEET_INDEX]
                    user_name = elem[config.NAME]
            elif cursor.count() > 1 and project:
                for elem in cursor:
                    if config.PROJECT_NAME in elem and config.SPREADSHEET_ID in elem and elem[
                            config.PROJECT_NAME].lower().strip(
                            ) == project.lower().strip():
                        spreadsheet_id = elem[config.SPREADSHEET_ID]
                        user_sheet_index = elem[config.USER_SHEET_INDEX]
                        user_name = elem[config.NAME]
                        break
        return {
            config.SPREADSHEET_ID: spreadsheet_id,
            config.USER_SHEET_INDEX: user_sheet_index,
            config.NAME: user_name
        }

    def fetch_project_name(self,
                           admin_email=None,
                           admin_id=None,
                           user_email=None,
                           user_id=None):
        project_name = None
        if (admin_email or admin_id) and (user_email or user_id):
            elem = None
            if admin_email and admin_id:
                elem = self.db[config.ADMIN_COLLECTION].find_one({
                    config.EMAIL: admin_email,
                    config.EMPLOYEE_ID: admin_id
                }, {config.PROJECTS_LIST: 1})
            if admin_email and not elem:
                elem = self.db[config.ADMIN_COLLECTION].find_one({
                    config.EMAIL: admin_email
                }, {config.PROJECTS_LIST: 1})
            if admin_id and not elem:
                elem = self.db[config.ADMIN_COLLECTION].find_one({
                    config.EMPLOYEE_ID: admin_id
                }, {config.PROJECTS_LIST: 1})

            if elem:
                if config.PROJECTS_LIST in elem:
                    for project in elem[config.PROJECTS_LIST]:
                        for user in project[config.USERS_LIST]:
                            if user_email and user_email == user[config.EMAIL]:
                                project_name = project[config.PROJECT_NAME]
                                break
                            elif user_id and user_id == user[
                                    config.EMPLOYEE_ID]:
                                project_name = project[config.PROJECT_NAME]
                                break
                        if project_name:
                            break
        return project_name

    def add_work_log(self, spreadsheet_id, date, task, hours=0, jira=None):
        self.update_data(
            config.USER_COLLECTION,
            query={config.SPREADSHEET_ID: spreadsheet_id},
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

    def mark_special_working(self, spreadsheet_id, date):
        self.update_data(
            config.USER_COLLECTION,
            query={config.SPREADSHEET_ID: spreadsheet_id},
            update_dict={
                "$set": {
                    "{}.{}.{}".format(config.WORK_DETAILS, date,
                                      config.SPECIAL_WORKING_FLAG): True
                }
            },
            upsert=False,
            multi=False)

    def add_leave(self, spreadsheet_id, date, ltype=None, lpurpose=None):
        self.update_data(
            config.USER_COLLECTION,
            query={config.SPREADSHEET_ID: spreadsheet_id},
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

    def approve_leave(self, spreadsheet_id, date):
        self.update_data(
            config.USER_COLLECTION,
            query={config.SPREADSHEET_ID: spreadsheet_id},
            update_dict={
                "$set": {
                    "{}.{}.{}".format(config.USER_LEAVES, date,
                                      config.LEAVE_APPROVED_STATUS): True
                }
            },
            upsert=False,
            multi=False)

    def add_wfh(self, spreadsheet_id, date, wfhtype=None, wfhpurpose=None):
        self.update_data(
            config.USER_COLLECTION,
            query={config.SPREADSHEET_ID: spreadsheet_id},
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

    def approve_wfh(self, spreadsheet_id, date):
        self.update_data(
            config.USER_COLLECTION,
            query={config.SPREADSHEET_ID: spreadsheet_id},
            update_dict={
                "$set": {
                    "{}.{}.{}".format(config.WORK_FROM_HOME, date,
                                      config.LEAVE_APPROVED_STATUS): True
                }
            },
            upsert=False,
            multi=False)

    def add_user(self,
                 project_name=None,
                 admin_email=None,
                 admin_id=None,
                 user_name=None,
                 user_id=None,
                 user_email=None):
        response_msg = None
        if (admin_email or admin_id) and user_email and user_id:
            elem = None
            if admin_email and admin_id:
                elem = self.db[config.ADMIN_COLLECTION].find_one({
                    config.EMAIL: admin_email,
                    config.EMPLOYEE_ID: admin_id
                }, {config.PROJECTS_LIST: 1,
                    '_id': 1})
            if admin_email and not elem:
                elem = self.db[config.ADMIN_COLLECTION].find_one({
                    config.EMAIL: admin_email
                }, {config.PROJECTS_LIST: 1,
                    '_id': 1})
            if admin_id and not elem:
                elem = self.db[config.ADMIN_COLLECTION].find_one({
                    config.EMPLOYEE_ID: admin_id
                }, {config.PROJECTS_LIST: 1,
                    '_id': 1})

            if elem:
                if config.PROJECTS_LIST in elem:
                    for pindex, project in enumerate(elem[
                            config.PROJECTS_LIST]):
                        if project[config.PROJECT_NAME] == project_name:
                            for user in project[config.USERS_LIST]:
                                if user_email and user_email == user[
                                        config.EMAIL]:
                                    response_msg = 'A user with same email already present in "{}" project'.format(
                                        project_name)
                                    break
                                elif user_id and user_id == user[
                                        config.EMPLOYEE_ID]:
                                    response_msg = 'A user with same employeeID already present in "{}" project'.format(
                                        project_name)
                                    break
                            if not response_msg:
                                self.update_data(
                                    config.ADMIN_COLLECTION,
                                    query={'_id': elem['_id']},
                                    update_dict={
                                        '$push': {
                                            "{}.{}.{}".format(
                                                config.PROJECTS_LIST, pindex,
                                                config.USERS_LIST):
                                            {
                                                config.EMAIL: user_email,
                                                config.EMPLOYEE_ID: user_id,
                                                config.NAME: user_name,
                                                config.USER_SHEET_INDEX: None
                                            }
                                        }
                                    },
                                    upsert=False,
                                    multi=False)
                                response_msg = "Cheers! User added successfully."
                            break
                    if not response_msg:
                        self.update_data(
                            config.ADMIN_COLLECTION,
                            query={'_id': elem['_id']},
                            update_dict={
                                '$push': {
                                    config.PROJECTS_LIST: {
                                        config.MONTH: None,
                                        config.YEAR: None,
                                        config.SPREADSHEET_ID: None,
                                        config.PROJECT_NAME: project_name,
                                        config.USERS_LIST: [{
                                            config.EMAIL: user_email,
                                            config.EMPLOYEE_ID: user_id,
                                            config.NAME: user_name,
                                            config.USER_SHEET_INDEX: None
                                        }],
                                        config.OLD_SHEETS: {}
                                    }
                                }
                            },
                            upsert=False,
                            multi=False)
                        response_msg = "Cheers! User and Project added successfully."
                else:
                    self.update_data(
                        config.ADMIN_COLLECTION,
                        query={'_id': elem['_id']},
                        update_dict={
                            '$set': {
                                config.PROJECTS_LIST: [{
                                    config.MONTH: None,
                                    config.YEAR: None,
                                    config.SPREADSHEET_ID: None,
                                    config.PROJECT_NAME: project_name,
                                    config.USERS_LIST: [{
                                        config.EMAIL: user_email,
                                        config.EMPLOYEE_ID: user_id,
                                        config.NAME: user_name,
                                        config.USER_SHEET_INDEX: None
                                    }],
                                    config.OLD_SHEETS: {}
                                }]
                            }
                        },
                        upsert=False,
                        multi=False)
                    response_msg = "Cheers! Added First Project and First User successfully."
            else:
                response_msg = "Admin not found with given details ::: First Add admin then try to add projects and users"
        else:
            response_msg = "Required parameter missing ((adminEmail OR adminID) AND userEmail AND userID)"
        return response_msg

    def remove_user(self,
                    project_name=None,
                    admin_email=None,
                    admin_id=None,
                    user_name=None,
                    user_id=None,
                    user_email=None):
        response_msg = None
        if (admin_email or admin_id) and (user_email or user_id):
            elem = None
            if admin_email and admin_id:
                elem = self.db[config.ADMIN_COLLECTION].find_one({
                    config.EMAIL: admin_email,
                    config.EMPLOYEE_ID: admin_id
                }, {config.PROJECTS_LIST: 1,
                    '_id': 1})
            if admin_email and not elem:
                elem = self.db[config.ADMIN_COLLECTION].find_one({
                    config.EMAIL: admin_email
                }, {config.PROJECTS_LIST: 1,
                    '_id': 1})
            if admin_id and not elem:
                elem = self.db[config.ADMIN_COLLECTION].find_one({
                    config.EMPLOYEE_ID: admin_id
                }, {config.PROJECTS_LIST: 1,
                    '_id': 1})

            if elem:
                if config.PROJECTS_LIST in elem:
                    for pindex, project in enumerate(elem[
                            config.PROJECTS_LIST]):
                        if project[config.PROJECT_NAME] == project_name:
                            user_index = None
                            for uindex, user in enumerate(project[
                                    config.USERS_LIST]):
                                if user_email and user_email == user[
                                        config.EMAIL]:
                                    response_msg = 'Removed user with email {}, employeeID {} from project "{}"'.format(
                                        user[config.EMAIL],
                                        user[config.EMPLOYEE_ID], project_name)
                                    user_index = uindex
                                    break
                                elif user_id and user_id == user[
                                        config.EMPLOYEE_ID]:
                                    response_msg = 'Removed user with email {}, employeeID {} from project "{}"'.format(
                                        user[config.EMAIL],
                                        user[config.EMPLOYEE_ID], project_name)
                                    user_index = uindex
                                    break
                            if user_index:
                                project[config.USERS_LIST].pop(user_index)
                                self.update_data(
                                    config.ADMIN_COLLECTION,
                                    query={'_id': elem['_id']},
                                    update_dict={
                                        '$set': {
                                            "{}.{}.{}".format(
                                                config.PROJECTS_LIST, pindex,
                                                config.USERS_LIST):
                                            project[config.USERS_LIST]
                                        }
                                    },
                                    upsert=False,
                                    multi=False)
                            else:
                                response_msg = "User not found with email {} or employeeID {} in project {}".format(
                                    user_email, user_id, project_name)
                            break
                    if not response_msg:
                        response_msg = "Project '{}' Not found please type a correct project name\n existing projects are {}".format(
                            project_name, [
                                x[config.PROJECT_NAME]
                                for x in elem[config.PROJECTS_LIST]
                            ])
                else:
                    response_msg = "Admin did not have any project So Please add projects first."
            else:
                response_msg = "Admin not found with given details ::: First Add admin then try to add projects and users"
        else:
            response_msg = "Required parameter missing ((adminEmail OR adminID) AND (userEmail OR userID))"
        return response_msg

    def new_user_record(self, month, year, spreadsheet_id, project_name,
                        admin_email, user_sheet_index, email, name, user_id):
        new_user = {
            config.MONTH: month,
            config.YEAR: year,
            config.SPREADSHEET_ID: spreadsheet_id,
            config.USER_SHEET_INDEX: user_sheet_index,
            config.EMAIL: email,
            config.NAME: name,
            config.PROJECT_NAME: project_name,
            config.ADMIN_EMAIL: admin_email,
            config.EMPLOYEE_ID: user_id,
            config.WORK_DETAILS: {},
            config.USER_LEAVES: {},
            config.WORK_FROM_HOME: {}
        }
        self.update_data(
            config.USER_COLLECTION,
            query={
                config.MONTH: month,
                config.YEAR: year,
                config.EMAIL: email,
                config.PROJECT_NAME: project_name
            },
            update_dict={"$set": new_user},
            upsert=True,
            multi=False)

    def append_new_users_in_userdb(self,
                                   admin_email=None,
                                   admin_id=None,
                                   projects=[]):
        appended_users = []
        if admin_email:
            elem = self.db[config.ADMIN_COLLECTION].find_one({
                config.EMAIL: admin_email
            })
        elif admin_id:
            elem = self.db[config.ADMIN_COLLECTION].find_one({
                config.EMPLOYEE_ID: admin_id
            })
        if elem:
            for project in elem[config.PROJECTS_LIST]:
                if not projects or project[config.PROJECT_NAME] in projects:
                    for user in project[config.USERS_LIST]:
                        self.new_user_record(
                            month=project[config.MONTH],
                            year=project[config.YEAR],
                            spreadsheet_id=project[config.SPREADSHEET_ID],
                            project_name=project[config.PROJECT_NAME],
                            admin_email=elem[config.EMAIL],
                            user_sheet_index=user[config.USER_SHEET_INDEX],
                            email=user[config.EMAIL],
                            name=user[config.NAME],
                            user_id=user[config.EMPLOYEE_ID])
                        appended_users.append(user)
        return appended_users
