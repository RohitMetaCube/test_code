import cherrypy
from skillset_extractor import nounphrase_extractor
from db_utils import DBUtils
from configurator import configurator
import time
from similarity_function import similarity_finder
from utils import format_skills, convert_encoding, find_all_ngrams_upto, create_lay_title_dict_and_lower_list
import nltk
from sklearn.externals import joblib
from filter_chain import filter_chain
from health_check import health_check
import os
from os.path import join
from os import listdir, rmdir
from shutil import move
import logging
from log_utils import OneLineExceptionFormatter
from SOCClassifier import SOCClassifierFactory
from utils import create_key
from norm_location_finder import create_location_maps
import csv


def save_to_file(filename,
                 context,
                 folder_path=configurator.commons.JOB_API_INIT_FILES_PATH):
    if folder_path.strip():
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        if folder_path.strip()[-1] != '/':
            folder_path = folder_path.strip() + "/"
    joblib.dump(context, folder_path + filename + "." +
                configurator.commons.MODEL_FILE_EXTENSION)
    return (" file <{}> successfully saved".format(
        folder_path + filename + "." +
        configurator.commons.MODEL_FILE_EXTENSION))


def load_file(filename,
              folder_path=configurator.commons.JOB_API_INIT_FILES_PATH):
    if folder_path.strip() and folder_path.strip()[-1] != '/':
        folder_path = folder_path.strip() + "/"
    return joblib.load(folder_path + filename + "." +
                       configurator.commons.MODEL_FILE_EXTENSION)


class norm_job(object):
    api_start_time = time.time()
    SKILLSET_SIZE = 30
    CONFIDENCE_THRESHOLD = 75
    dbutils = DBUtils(configurator.commons.MONGODB_HOST)
    universal_skill_set = dbutils.create_resume_posting_universal_skill_set(
        SKILLSET_SIZE)
    ngram_limit = 1
    npe = nounphrase_extractor()
    sf = similarity_finder()

    JOBS_PARAMETER = "jobs"
    JOB_TITLE_PARAMETER = "title"
    JOB_DESCRIPTION_PARAMETER = "description"
    PREVIOUS_JOB_TITLE_PARAMETER = "previous_title"
    PREVIOUS_JOB_DESCRIPTION_PARAMETER = "previous_description"
    SOC_HINT_PARAMETER = "soc_hint"
    sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

    for skill in universal_skill_set:
        l = len(skill.split())
        if l > ngram_limit:
            ngram_limit = l

    def __init__(self):
        LAY_TITLE_LIST_NAME = 'lay_title_list'
        LAY_TITLE_DICT_NAME = 'lay_title_dict'
        SIMILAR_TITLE_DICT_NAME = 'title_to_similar_title_dict'
        CITY_LIST = 'city_list'
        STATE_LIST = 'state_list'
        STATE_CODES = 'state_codes'
        SOC_MASTER_DICT_NAME = 'soc_master_dict'
        SOC_MAPPING_NAME = 'soc_mapping'
        SIMILAR_DICT_NAME = 'similar_title_dict'

        try:
            self.soc_master_dict = load_file(SOC_MASTER_DICT_NAME)
            self.soc_mapping = load_file(SOC_MAPPING_NAME)
            self.similar_title_dict = load_file(SIMILAR_DICT_NAME)
            self.lay_title_list = load_file(LAY_TITLE_LIST_NAME)
            self.title_to_similar_title_dict = load_file(
                SIMILAR_TITLE_DICT_NAME)
            self.lay_title_dict = load_file(LAY_TITLE_DICT_NAME)
            self.city_list = load_file(CITY_LIST)
            self.state_list = load_file(STATE_LIST)
            self.state_codes = load_file(STATE_CODES)
        except:
            [self.soc_master_dict, self.lay_title_list, self.soc_mapping
             ] = norm_job.dbutils.create_all_lay_title_mappings()
            [self.similar_title_dict, self.title_to_similar_title_dict
             ] = norm_job.dbutils.create_all_similar_title_mappings()

            [self.lay_title_dict, self.lay_title_list
             ] = create_lay_title_dict_and_lower_list(self.lay_title_list)
            res = create_lay_title_dict_and_lower_list(
                self.title_to_similar_title_dict, stem_key=True)
            self.lay_title_dict.update(res[0])
            self.title_to_similar_title_dict = res[1]
            del res

            results = create_location_maps(norm_job.dbutils)
            self.city_list = results["city_list"]
            self.state_list = results["state_list"]
            self.state_codes = results["state_codes"]

            try:
                folder = configurator.commons.JOB_API_INIT_FILES_PATH
                if folder:
                    if folder.strip()[-1] != '/':
                        folder = folder.strip() + "/"
                    if not os.path.exists(folder):
                        os.makedirs(folder)
                temp_folder_path = folder + str(os.getpid()) + "_" + str(
                    time.time())
                try:
                    logging.info(
                        save_to_file(LAY_TITLE_DICT_NAME, self.lay_title_dict,
                                     temp_folder_path))
                    logging.info(
                        save_to_file(LAY_TITLE_LIST_NAME, self.lay_title_list,
                                     temp_folder_path))
                    logging.info(
                        save_to_file(SIMILAR_TITLE_DICT_NAME,
                                     self.title_to_similar_title_dict,
                                     temp_folder_path))
                    logging.info(
                        save_to_file(CITY_LIST, self.city_list,
                                     temp_folder_path))
                    logging.info(
                        save_to_file(STATE_LIST, self.state_list,
                                     temp_folder_path))
                    logging.info(
                        save_to_file(STATE_CODES, self.state_codes,
                                     temp_folder_path))
                    logging.info(
                        save_to_file(SOC_MASTER_DICT_NAME,
                                     self.soc_master_dict, temp_folder_path))
                    logging.info(
                        save_to_file(SOC_MAPPING_NAME, self.soc_mapping,
                                     temp_folder_path))
                    logging.info(
                        save_to_file(SIMILAR_DICT_NAME, self.
                                     similar_title_dict, temp_folder_path))
                except Exception as e:
                    root.exception(e)
                # if folder exists (may be due to parallel processes) then remove current temporary folder
                ''' Rename directory '''
                if os.path.exists(temp_folder_path):
                    for filename in listdir(join(folder, temp_folder_path)):
                        move(
                            join(folder, temp_folder_path, filename),
                            join(folder, filename))
                    rmdir(temp_folder_path)
            except Exception as e:
                root.exception(e)
                pass

        remove_cities = [
            'teller', 'home', 'cook', 'grill', 'helper', 'industrial', 'mobile'
        ]
        for city in remove_cities:
            if city in self.city_list:
                del self.city_list[city]

        self.soc_lay_title_token_list = {}
        for soc, lts in self.lay_title_list.items():
            self.soc_lay_title_token_list[soc] = {}
            for lt in lts:
                for token in set(lt.split()):
                    if token not in self.soc_lay_title_token_list[soc]:
                        self.soc_lay_title_token_list[soc][token] = set()
                    self.soc_lay_title_token_list[soc][token].add(lt)
                if lt in self.title_to_similar_title_dict:
                    for st in self.title_to_similar_title_dict[lt]:
                        for token in set(st.split()):
                            if token not in self.soc_lay_title_token_list[soc]:
                                self.soc_lay_title_token_list[soc][
                                    token] = set()
                            self.soc_lay_title_token_list[soc][token].add(st)
        '''Load Model'''
        try:
            self.model = SOCClassifierFactory.create_classifier(
                configurator.commons.JOB_POSTING_CLF_NAME)
        except Exception as e:
            root.exception(e)
            exit()

        f = open('dictionaries/selected_ngrams_for_driver.csv', 'rb')
        fr = csv.reader(f, delimiter='\t')
        self.driver_ngrams_set = set(
            [row[0] for row in fr if (row[0] and row[0].strip())])
        ltm_cursor = norm_job.dbutils.fetch_data(
            configurator.commons.LAY_TITLE_MASTER, 'cursor',
            {'soc_code': {
                '$regex': '^53-'
            }}, {'soc_code': 1})
        self.driver_soc_codes = [(ltm_elem['soc_code'], 100)
                                 for ltm_elem in ltm_cursor]

        root.info("API Start Time= {}s".format(time.time() -
                                               norm_job.api_start_time))

    def extract_soc_code(self, text, prefix, suffix):
        if text.startswith(prefix) and text.endswith(suffix):
            return text[len(prefix):-len(suffix)]
        return None

    @staticmethod
    def fetch_closest_lay_title(lay_title_list, soc_lay_title_token_list,
                                soc_code_tuple, job_title, job_description):
        closest_lay_title = configurator.commons.DEFAULT_CLOSEST_LAY_TITLE
        default_soc = soc_code_tuple[0]
        top_soc = soc_code_tuple[0]
        valid_lay_titles = set()
        tokens = job_title.split()
        for soc_code in soc_code_tuple:
            if soc_code in soc_lay_title_token_list:
                for token in tokens:
                    if token in soc_lay_title_token_list[soc_code]:
                        valid_lay_titles = valid_lay_titles.union(
                            soc_lay_title_token_list[soc_code][token])
        if len(valid_lay_titles):
            closest_lay_title = norm_job.sf.find_closest_lay_title(
                valid_lay_titles, job_title, job_description)
            for soc in soc_code_tuple:
                if soc in lay_title_list and closest_lay_title in set(
                        lay_title_list[soc]):
                    default_soc = soc
                    break
        return closest_lay_title, default_soc, top_soc

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def normalize(self, **other_params):
        cherrypy.response.headers['Content-Type'] = "application/json"
        params = {}
        if cherrypy.request.method == "POST":
            params = cherrypy.request.json
        error_message = str()
        error_flag = False
        job_description = ""
        batch_size = 0
        total_time = time.time()

        if norm_job.JOBS_PARAMETER not in params:
            error_flag = True
            error_message = configurator.commons.MALFORMED_REQUEST_ERROR_MESSAGE
        else:
            jobs = params[norm_job.JOBS_PARAMETER]
            job_array = []
            skill_array = []
            responses = []
            bypass_array = []
            batch_size = len(jobs)
            for job in jobs:
                try:
                    filtered_title = job[norm_job.JOB_TITLE_PARAMETER]
                    if "instead of" in filtered_title.lower():
                        filtered_title = filtered_title[:filtered_title.lower(
                        ).find("instead of")].strip()
                    filtered_title = create_key(filtered_title, self.city_list,
                                                self.state_list,
                                                self.state_codes)
                    job[norm_job.JOB_TITLE_PARAMETER] = filtered_title
                except:
                    filtered_title = ""
                job_description = ""
                if norm_job.JOB_DESCRIPTION_PARAMETER in job:
                    job_description = job[norm_job.JOB_DESCRIPTION_PARAMETER]
                title_ngrams = find_all_ngrams_upto(filtered_title.lower(), 4)
                if title_ngrams.intersection(self.driver_ngrams_set):
                    bypass_array.append(1)
                else:
                    job_array.append((filtered_title, job_description))
                    bypass_array.append(0)
                imp_skills = set()

                if job_description:
                    sentences = norm_job.sent_detector.tokenize(
                        job_description)
                    for sentence in sentences:
                        lower_sentence = sentence.lower()
                        sentence_n_grams = find_all_ngrams_upto(
                            lower_sentence, norm_job.ngram_limit)
                        imp_skills.update(
                            sentence_n_grams.intersection(
                                norm_job.universal_skill_set))
                skill_array.append(imp_skills)

            start_time = time.time()
            prediction_array = self.model.predict(job_array)
            root.info(
                "Context Free classification for {0} points done in {1}s".
                format(len(prediction_array), time.time() - start_time))
            del job_array
            #             root.info(prediction_array)

            start_time = time.time()
            for point_index, selector_value in enumerate(bypass_array):
                if selector_value:
                    soc_codes_with_conf = self.driver_soc_codes
                else:
                    soc_codes_with_conf = prediction_array.pop(0)
                soc_codes = [
                    soc[0]
                    for soc in sorted(
                        soc_codes_with_conf, key=lambda k: k[1], reverse=True)
                ]
                try:
                    job_title = jobs[point_index][norm_job.JOB_TITLE_PARAMETER]
                    if "instead of" in job_title.lower():
                        job_title = job_title[:job_title.lower().find(
                            "instead of")].strip()
                except:
                    error_flag = True
                    error_message = configurator.commons.MALFORMED_REQUEST_ERROR_MESSAGE
                if not error_flag:
                    response_json = {}
                    response_json["index"] = point_index
                    response_json["clean_original_title"] = format_skills(jobs[
                        point_index][norm_job.JOB_TITLE_PARAMETER])
                    response_json["soc_code"] = ''
                    response_json["confidence"] = 0
                    response_json["closest_lay_title"] = ''
                    response_json["major_group_string"] = ''
                    response_json["skills"] = list(skill_array[point_index])

                    if not soc_codes:
                        ''' The given job posting could not be normalized using our standard algorithm.
                        We should use the soc_hint parameter present here to see if we can find a nearby
                        title in the given hint SOC code.'''
                        if norm_job.SOC_HINT_PARAMETER in jobs[point_index]:
                            soc_hint = jobs[point_index][
                                norm_job.SOC_HINT_PARAMETER]
                            if soc_hint in self.soc_mapping:
                                ''' This is a valid SOC Code '''
                                associated_soc_codes = self.soc_mapping[
                                    soc_hint]
                                soc_codes = list(associated_soc_codes)
                                root.info(
                                    "Hinted {} hence, Comparing Against Codes {}".
                                    format(soc_hint, soc_codes))
                            else:
                                ''' This is an invalid SOC Code and we can't do much about it. '''
                                root.info(
                                    "No matching SOC Code found in soc_hint {}. Cannot normalize.".
                                    format(soc_hint))
                    if soc_codes:
                        key_string = filter_chain.apply(
                            convert_encoding(job_title), is_title=True)[1]
                        closest_lay_title_tuple = norm_job.fetch_closest_lay_title(
                            self.lay_title_list, self.soc_lay_title_token_list,
                            soc_codes, key_string, "")
                        major_group_string = configurator.commons.DEFAULT_MAJOR_GROUP_STRING
                        if closest_lay_title_tuple[1] in self.soc_master_dict:
                            major_group_string = self.soc_master_dict[
                                closest_lay_title_tuple[1]][
                                    'major_group_string']
                        lay_title = convert_encoding(closest_lay_title_tuple[
                            0])
                        if lay_title in self.lay_title_dict:
                            lay_title = self.lay_title_dict[lay_title]
                            if lay_title in self.similar_title_dict:
                                lay_title = self.similar_title_dict[lay_title]
                        response_json["soc_code"] = closest_lay_title_tuple[1]
                        response_json["confidence"] = int(
                            dict(soc_codes_with_conf)[closest_lay_title_tuple[
                                1]])
                        response_json['top_soc'] = closest_lay_title_tuple[2]
                        response_json["closest_lay_title"] = lay_title
                        response_json[
                            "major_group_string"] = major_group_string
                else:
                    response_json = {
                        "error_code":
                        configurator.commons.MALFORMED_REQUEST_ERROR_STATUS,
                        "message": error_message
                    }
                responses.append(response_json)
                error_flag = False
                if (point_index + 1) % 1000 == 0:
                    root.info("{0} points done in {1}s".format(
                        point_index, time.time() - start_time))
                    start_time = time.time()
            responses_object = {"normalized_jobs": responses}
        if error_flag:
            cherrypy.response.status = configurator.commons.MALFORMED_REQUEST_ERROR_STATUS
            responses_object = {
                "error_code":
                configurator.commons.MALFORMED_REQUEST_ERROR_STATUS,
                "message": error_message
            }

        root.info("{0} points done in {1}s".format(batch_size,
                                                   time.time() - total_time))

        return responses_object


''' Initializing the web server '''
if __name__ == '__main__':
    logging_handler = logging.StreamHandler()
    log_format = OneLineExceptionFormatter(
        configurator.commons.LOG_FORMAT_STRING,
        configurator.commons.LOG_TIME_FORMAT)
    logging_handler.setFormatter(log_format)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(logging_handler)
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': configurator.commons.JOB_NORMALIZATION_API_PORT,
        'server.thread_pool':
        configurator.commons.JOB_NORMALIZATION_API_THREADS,
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'response.timeout':
        configurator.commons.JOB_NORMALIZATION_API_RESPONSE_TIMEOUT,
        'server.socket_queue_size':
        configurator.commons.JOB_NORMALIZATION_API_SOCKET_QUEUE_SIZE,
        'engine.timeout_monitor.on': False,
        'log.screen': False,
        'log.access_file': '',
        'log.error_log_propagate': False,
        'log.accrss_log.propagate': False,
        'log.error_file': ''
    })

    cherrypy.tree.mount(
        norm_job(),
        configurator.commons.JOB_NORMALIZATION_API_CONTEXT,
        config={'/': {}})
    cherrypy.tree.mount(
        health_check(),
        configurator.commons.HEARTBEAT_CONTEXT,
        config={'/': {}})
    cherrypy.engine.start()
    cherrypy.engine.block()
