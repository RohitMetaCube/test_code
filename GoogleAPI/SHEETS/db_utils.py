from pymongo import MongoClient, ASCENDING
import config


class mongoDB:
    def __init__(self,
                 host=config.MONGODB_HOST,
                 port=config.MONGODB_PORT,
                 db_name=config.MONGODB_NAME):
        self.db = MongoClient(host, port)[db_name]
        self.ensure_indexes(
            config.TIMESHEET_COLLECTION,
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

    def fetch_spreadsheet_id(self,
                             month=None,
                             year=None,
                             email=None,
                             project=None):
        spreadsheet_id = None
        if month and year and email:
            cursor = self.db[config.TIMESHEET_COLLECTION].find({
                config.ADMIN_EMAIL: email,
                config.YEAR: year,
                config.MONTH: month
            }, {config.SPREADSHEET_ID: 1,
                config.PROJECT_NAME: 1})
            if cursor.count() == 1:
                elem = cursor[0]
                if config.SPREADSHEET_ID in elem:
                    spreadsheet_id = elem[config.SPREADSHEET_ID]
            elif cursor.count() > 1 and project:
                for elem in cursor:
                    if config.PROJECT_NAME in elem and config.SPREADSHEET_ID in elem and elem[
                            config.PROJECT_NAME].lower().strip(
                            ) == project.lower().strip():
                        spreadsheet_id = elem[config.SPREADSHEET_ID]
                        break
        return spreadsheet_id
