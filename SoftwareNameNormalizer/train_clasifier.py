# -*- coding: utf-8 -*-
import os
from db_utils import DBUtils
from configurator import configurator
import math
import random
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import SGDClassifier
# from sklearn.grid_search import GridSearchCV
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn import metrics
from sklearn.externals import joblib
from utils import cnv
from pymongo import ASCENDING
from BeautifulSoup import BeautifulSoup
import re
import csv
import copy


def rcnv(t):
    t = cnv(t)
    if not t:
        t = ''
    return t


MODEL_PATH = '/mnt/data/rohit/section_spliter_model/SGD_Special_Tokens_all/'


def save_to_file(filename, context, folder_path=MODEL_PATH):
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


def load_file(filename, folder_path=MODEL_PATH):
    if folder_path.strip() and folder_path.strip()[-1] != '/':
        folder_path = folder_path.strip() + "/"
    return joblib.load(folder_path + filename + "." +
                       configurator.commons.MODEL_FILE_EXTENSION)


def read_label_tokens(file_path='/mnt/data/rohit/section_headers.csv'):
    f = open(file_path, 'rb')
    dialect = csv.Sniffer().sniff(f.readline(), delimiters='\t,')
    f.seek(0)
    fr = csv.reader(f, delimiter=dialect.delimiter)
    token_label_map = {}
    for row in fr:
        section_heading = row[0].lower()
        label = row[2]
        token_label_map[section_heading] = label
    return token_label_map


def create_sample_data_set(training_collection_name, limit=50000):
    data = []
    targets = []
    labels = db.distinct_data(training_collection_name, 'label')
    for label in labels:
        counter = 0
        all_counter = 0
        cursor = db.fetch_data(
            training_collection_name, query={'label': label})
        for elem in cursor:
            text = elem['header'] + elem['text']
            header = elem['header'].lower()
            if len(re.sub("\W+", " ", elem['header']).split()) < 6 and len(
                    text.split()) > 50:
                labels = set(
                    [sl for st, sl in token_label_map.items() if st in header])
                if len(labels) == 1:
                    data.append(elem)
                    targets.append(elem['label'])
                    counter += 1
            if counter >= limit:
                break
            all_counter += 1
            if all_counter % 10000 == 0:
                print all_counter
        print all_counter
        print "Done Label: {}".format(label)
    return_object = {}
    return_object['data'] = data
    return_object['targets'] = targets
    print "Done Data Reading for Collection: {}".format(
        training_collection_name)
    return return_object


class DataCleaner:
    def __init__(self):
        self.pattern1 = re.compile("([ ]*\.[ ]*)+")
        self.pattern2 = re.compile(" +")
        pass

    def remove_tags(self, text):
        soup = BeautifulSoup(text, convertEntities=BeautifulSoup.HTML_ENTITIES)
        text = ' '.join(soup.findAll(text=True))
        #text = self.pattern1.sub(". ", text)
        text = re.sub("\W+", ' ', text.lower())
        text = self.pattern2.sub(" ", text)

        return text

    def replace_special_tokens(self, data_dict):
        replacements = {}
        replacements[data_dict['company_original']] = '__COMPANY__'
        replacements[data_dict['company_normalized']] = '__COMPANY__'
        replacements[data_dict['title_original']] = '__TITLE__'
        replacements[data_dict['title_normalized']] = '__TITLE__'
        replacements[data_dict['city']] = '__CITY__'
        replacements[data_dict['state']] = '__STATE__'

        text = data_dict['text'].lower()
        for replacement_key, replacement_value in replacements.items():
            if replacement_key:
                text = text.replace(replacement_key.lower(), replacement_value)
        data_dict['text'] = text

        text = data_dict['header'].lower()
        for replacement_key, replacement_value in replacements.items():
            if replacement_key:
                text = text.replace(replacement_key.lower(), replacement_value)
        data_dict['header'] = text

    def transform(self, data, y=None):
        result_data = []
        for d_t in data:
            self.replace_special_tokens(d_t)
            d = (" ".join([
                "HEADER_{}".format(rcnv(x))
                for x in self.remove_tags(d_t['header']).split()
            ]) + " ") * 2 + rcnv(self.remove_tags(d_t['text']))
            result_data.append(d)
        return result_data

    def fit(self, data, target):
        return self


def train_model(training_collection_name):
    data_dict = create_sample_data_set(training_collection_name)
    text_clf = Pipeline(
        [('preprocessor', DataCleaner()),
         ('vect', CountVectorizer(stop_words='english')),
         ('tfidf', TfidfTransformer()), ('feature_section', TruncatedSVD(
             n_components=500,
             algorithm='randomized',
             n_iter=10,
             random_state=42)), ('clf', SGDClassifier(loss="modified_huber"))])
    text_clf = text_clf.fit(data_dict['data'], data_dict['targets'])

    print save_to_file("Model", text_clf)


def test_model(test_collection_name):
    text_clf = load_file("Model")
    test_data = create_sample_data_set(test_collection_name, limit=10000)

    predicted = text_clf.predict(test_data['data'])
    print "Accuracy: {}%".format(
        np.mean(predicted == test_data['targets']) * 100)
    print(metrics.classification_report(
        test_data['targets'],
        predicted,
        target_names=list(set(test_data['targets']))))
    print metrics.confusion_matrix(test_data['targets'], predicted)
    f = open('/mnt/data/rohit/mismatch_predictions.csv', 'wb')
    f.write("Prediction\tLabel\tHeader\tText\n")
    mismatch_count = 0
    total_count = 0
    for i, prediction in enumerate(predicted):
        label = test_data['targets'][i]
        header = rcnv(test_data['data'][i]['header'])
        text = rcnv(test_data['data'][i]['text'])
        if label != prediction:
            mismatch_count += 1
            f.write("{}\t{}\t{}\t{}\n".format(prediction, label, header, text))
        total_count += 1
    f.close()
    print "Total Test Count: {}, Mismatch Count: {}".format(total_count,
                                                            mismatch_count)
    print "Done"


def test_model_on_manual_data(test_data):
    text_clf = load_file("Model")
    predicted = text_clf.predict(test_data)
    for i, prediction in enumerate(predicted):
        print "Prediction: {},  Header: {}".format(prediction, test_data[i][0])
    print "Done"


def create_collection_and_index(collection_name,
                                index_list=[('label', ASCENDING)]):
    db.db[collection_name].ensure_index(index_list)


def label_counter(collection_name, training_part_fraction):
    label_count_map = {}
    count = 0
    cursor = db.fetch_data(collection_name)
    for elem in cursor:
        for label in set([data['label'] for data in elem['paragraphs']]):
            if label not in label_count_map:
                label_count_map[label] = {}
                label_count_map[label]['total_records'] = 0
                label_count_map[label]['training_records_count'] = 0
                label_count_map[label]['indexes'] = []
                label_count_map[label]['counter'] = 0
            label_count_map[label]['total_records'] += 1
        count += 1
        if count % 10000 == 0:
            print count
    for label, count_dict in label_count_map.items():
        count_dict['training_records_count'] = int(
            math.ceil(count_dict['total_records'] * training_part_fraction))
        indexes = range(count_dict['total_records'])
        random.shuffle(indexes)
        count_dict['indexes'] = indexes
        print "Label: {}, Total Records: {}, Training Records: {}, Test Records: {}".format(
            label, count_dict['total_records'],
            count_dict['training_records_count'],
            count_dict['total_records'] - count_dict['training_records_count'])
        print "first 5 indexes: {}".format(count_dict['indexes'][:5])
    return label_count_map


def training_test_spliter(collection_name, training_collection_name,
                          test_collection_name, non_labeled_collection_name,
                          training_part_fraction):
    labels = label_counter(collection_name, training_part_fraction)
    cursor = db.fetch_data(collection_name, query={}, projection_list={})
    count = 0
    for elem in cursor:
        test_records = []
        train_records = []
        non_labeled_records = []
        new_entry = {}
        new_entry['company_original'] = elem['company_original']
        new_entry['company_normalized'] = elem['company_normalized']
        new_entry['title_original'] = elem['title_original']
        new_entry['title_normalized'] = elem['title_normalized']
        new_entry['state'] = elem['state']
        new_entry['city'] = elem['city']
        new_entry['source'] = elem['source']
        new_entry['socCode'] = elem['socCode']
        new_entry['majorPriority'] = elem['majorPriority']

        for data in elem['paragraphs']:
            if labels[data['label']]['counter'] < labels[data['label']][
                    'total_records']:
                new_entry_data = copy.copy(new_entry)
                new_entry_data.update(data)
                if data['label'] and labels[data['label']]['indexes'][labels[
                        data['label']]['counter']] < labels[data['label']][
                            'training_records_count']:
                    train_records.append(new_entry_data)
                elif data['label']:
                    test_records.append(new_entry_data)
                else:
                    non_labeled_records.append(new_entry_data)
                labels[data['label']]['counter'] += 1

        if train_records:
            db.insert_records(training_collection_name, train_records)
        if test_records:
            db.insert_records(test_collection_name, test_records)
        if non_labeled_records:
            db.insert_records(non_labeled_collection_name, non_labeled_records)
        count += 1
        if count % 1000 == 0:
            print count
    print count
    create_collection_and_index(training_collection_name)
    create_collection_and_index(test_collection_name)
    print "Done"


def clean_data_set(collection_name,
                   min_token_len=50,
                   min_header_len=5,
                   max_header_tokens=8):
    removable_ids = []
    label_wise_removal = {}
    cursor = db.fetch_data(collection_name)
    count = 0
    for elem in cursor:
        label = elem['label']
        if label not in label_wise_removal:
            label_wise_removal[label] = {}
            label_wise_removal[label]['removed'] = 0
            label_wise_removal[label]['total'] = 0
        label_wise_removal[label]['total'] += 1
        header = re.sub("\W+", " ", elem['header'])
        if len(re.sub("\W+", "", elem['text'])) < min_token_len or len(
                header.replace(' ', '')) < min_header_len and len(header.split(
                )) > max_header_tokens:
            removable_ids.append(elem['_id'])
            label_wise_removal[label]['removed'] += 1
        count += 1
        if count % 10000 == 0:
            print count, len(removable_ids)
    print count, len(removable_ids)
    for _id in removable_ids:
        db.remove_entry(collection_name, query_dict={"_id": _id})
    print "DONE CLEANING ON COLLECTION: {}, REMOVED {} ENTRIES".format(
        collection_name, len(removable_ids))
    for label, removed_object in label_wise_removal.items():
        print "Label: {}, Total: {}, Removed: {}".format(
            label, removed_object['total'], removed_object['removed'])


if __name__ == "__main__":
    db = DBUtils(db_name='test_db', host="localhost")
    collection_name = 'paragraphs'  #"responsibilities_paragraphs_3"
    training_collection_name = "training_paragraphs"
    test_collection_name = "test_paragraphs"
    non_labeled_collection_name = "non_labeled_paragraphs"
    training_part_fraction = 0.7

#     training_test_spliter(collection_name, training_collection_name, test_collection_name, non_labeled_collection_name, training_part_fraction)
#     clean_data_set(training_collection_name)
#     clean_data_set(test_collection_name)

#     token_label_map = read_label_tokens()
#     train_model(training_collection_name)
#     test_model(test_collection_name)

#     test_data = [
#         ("WHO WE ARE", "Founded in 1925 by George Godber and Carl Speer, Trojan Battery Company is the world's leading manufacturer of deep-cycle batteries. From deep-cycle flooded batteries to deep-cycle AGM and gel batteries, Trojan has shaped the world of deep-cycle battery technology with more than over 90 years of battery manufacturing experience. Trojan Battery Company's core values focus on our commitment to developing innovative environmentally friendly energy storage solutions that effectively meet customer needs, and serve the global community at large. Trojan values the integrity of our business relations, the quality of our deep-cycle technology, reliability of our products and services, as well as the professional growth of our team members."),
#         ("ABOUT THE ROLE", "Trojan Battery Company is looking for an experienced Senior Product Engineer to join our team. The Senior Product Engineering may be assigned to either of the Product Engineering groups (Battery Engineering, Advanced Energy Storage or Systems Engineering.) This position will provide you with the opportunity to partner with a dynamic and analytical group who set a high bar for innovation and success in a high-growth environment. To get there, we need exceptionally talented, bright, and driven people. If you'd like to help, this is your chance to make history by joining Trojan Battery Company. As the Senior Product Engineer you will be responsible for providing a broad knowledge and experience base in support of Trojan Battery Company product development and commercialization. You will assume a leadership role in some assigned programs, projects or tasks. As the Senior Product Engineer you will also support the fulfillment of the Trojan Battery Company Product Lifecycle Management processes from Product Requirements Documents (PRD) through all phase of design and continuing support for assigned existing or emerging products. This person must thrive in an innovative, fast-paced environment, can roll up their sleeves, work hard, have fun, and get the job done."), 
#         ("THE DAY TO DAY", "Contribute to project/program technical requirements - Product Requirements Documents (PRD) in response to given Market Requirements Documents (MRD). Drive and execute product or component design projects/programs to meet given PRD's including the development of the Concept of Operations and all phases of design from concept to production release. Drive and execute Engineering Validation Testing (EVT) and Design Validation Testing (DVT) of assigned projects/programs. Participate in project and program stage gate meetings as required. Participate in and lead design review and deep-dive technical sessions Author and coordinate Engineering Studies and produce required reports including authoritative conclusions and recommendations. Participate in and lead cross-functional teams consisting of internal and/or external resources to accomplish tasks related to product development. Prepare engineering reports and procedures. Interact directly with suppliers, customers and senior staff of other TBC departments as required. Provide evaluations of new/competitive designs and make recommendations for product improvements and or new products driving innovation through the department and cross functionally. Responsible for key tasks defined in project schedules including regular status reporting and meeting timeline/budgetary constraints. Provide guidance to technicians and test engineers performing field or laboratory testing. Participate in recruiting efforts for the department and the company by participating in interviews and round table candidate discussions. Mentor and support more junior department members by providing technical guidance and leadership"), 
#         ("EDUCATION and/or EXPERIENCE", "Bachelor's degree in chemical, mechatronics, systems or mechanical engineering required 6 years minimum of engineering or battery-related experience Licensed Professional Engineer preferred but not required. Experience working in cross functional teams involved in successful product design, development and launch for consumer, industrial and/or commercial products. Preference for experience within a formal Product Lifecycle Management process Experience in the design, validation, release and ongoing support of consumer, industrial and/or commercial products or components Experience within technology commercialization projects Experience within a technology manufacturing organization Experience within a formal configuration management system Understanding of international and national standards (UL, BCI, IEEE, IEC, etc.) Excellent technical skills and deep experience spanning multiple related specialties including CAD modeling and engineering drawing generation, materials selection, prototype development, manufacturing processes and DFx. High level of computer competency including proficiency in project management software and most Microsoft office applications Very high level of proficiency in MS Excel for data analysis and report generation Proficient technical writer"),
#         ("PERKS and BENEFITS", "A variety of Medical, Dental, and Vision Plans Section 125 Cafeteria Plan 401(k)/401k Roth Disability Income – specific locations and/or classification Group Legal Services Corporate 529 College Savings Plan Tuition Reimbursement Credit Union Membership Blue Heart Campaign- An awareness raising initiative to fight human trafficking and its impact on society A variety of Employee Discounts Employee Wellness Programs Volunteer and Company Sponsored Philanthropy Trips Company Description At Trojan Battery we provide clean and reliable energy solutions that enhance they way people live and work around the world. As a leading energy storage company delivering world class solutions for over 91 years, we are looking for talent to join our growing company as we innovate the energy storage market. We know our success is built on the ability to encourage and support the success of each employee.")
#     ]
#     test_model_on_manual_data(test_data)
