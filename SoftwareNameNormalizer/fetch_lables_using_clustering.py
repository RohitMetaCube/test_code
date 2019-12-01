from pymongo import MongoClient
import config
import xlrd
import csv
from sklearn.cluster import KMeans
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import os
from sklearn.externals import joblib
from utils import preprocess_organization, cnv

db = MongoClient(config.MONGO_HOST, config.MONGO_PORT)[config.MONGO_DB_NAME]

MODEL_PATH = 'datasets/Models/'


def save_to_file(filename, context, folder_path=MODEL_PATH):
    if folder_path.strip():
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        if folder_path.strip()[-1] != '/':
            folder_path = folder_path.strip() + "/"
    joblib.dump(context,
                folder_path + filename + "." + config.MODEL_FILE_EXTENSION)
    return (" file <{}> successfully saved".format(
        folder_path + filename + "." + config.MODEL_FILE_EXTENSION))


def load_file(filename, folder_path=MODEL_PATH):
    if folder_path.strip() and folder_path.strip()[-1] != '/':
        folder_path = folder_path.strip() + "/"
    return joblib.load(folder_path + filename + "." +
                       config.MODEL_FILE_EXTENSION)


def read_excel_and_move_data_in_mongo(file_path='datasets/entry-software.xls'):
    book = xlrd.open_workbook(file_path, on_demand=True)
    work_sheet = book.sheet_by_index(0)
    header = list(work_sheet.row_values(7))
    count = 0
    for i in range(8, work_sheet.nrows):
        row = work_sheet.row_values(i)
        json_data = dict(
            [(k, v) for k, v in map((lambda k, v: (k, v)), header, row) if k])
        db[config.SOFTWARE_COLLECTION].insert_one(json_data)
        count += 1
        if count % 100 == 0:
            print count
    print count


def create_clusters(data,
                    number_of_clusters=500,
                    model_file_name="KMeans",
                    tfidf_vector_file_name="TfIdfVector"):
    pl = TfidfVectorizer(
        max_df=0.5,
        max_features=number_of_clusters,
        min_df=1,
        stop_words="english",
        use_idf=False)
    data = pl.fit_transform(data)
    kmeans = KMeans(n_clusters=number_of_clusters, random_state=0).fit(data)
    save_to_file(model_file_name, kmeans)
    save_to_file(tfidf_vector_file_name, pl)
    test_model(model_file_name, tfidf_vector_file_name, number_of_clusters)


def data_cleaner(data,
                 software_field="Software Title",
                 first_n_tokens=10,
                 organization=False):
    if organization:
        data = [
            " ".join(
                preprocess_organization(x[software_field]).split()
                [:first_n_tokens]) for x in data
        ]
    else:
        data = [
            "__COMPANY__{} __CATEGORY__{} __OS__{} {}".format(
                x['publisherClusterNumber'], x['Category'], x['OS'], " ".join(
                    re.sub("update for", " ", re.sub("[^a-zA-Z]+", " ", x[software_field].lower())).split()
                    [:first_n_tokens])) for x in data
        ]
    return data


def test_model(model_file_name="KMeans",
               tfidf_vector_file_name="TfIdfVector",
               number_of_clusters=100):
    kmeans = load_file(model_file_name)
    pl = load_file(tfidf_vector_file_name)

    print kmeans.labels_
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = pl.get_feature_names()
    for i in range(number_of_clusters):
        print("Cluster %d:" % i),
        for ind in order_centroids[i, :10]:
            print(' %s' % terms[ind]),
        print
    print kmeans.predict(pl.transform(["Adobe Flash Player", "Python NLTK"]))
    print kmeans.cluster_centers_


def set_cluster_number(software_field="Software Title",
                       cluster_field="clusterNumber",
                       model_file_name="KMeans",
                       tfidf_vector_file_name="TfIdfVector",
                       first_n_tokens=10,
                       organization=False):
    kmeans = load_file(model_file_name)
    pl = load_file(tfidf_vector_file_name)
    cursor = db[config.SOFTWARE_COLLECTION].find()
    count = 0
    for software in cursor:
        data = data_cleaner(
            [software],
            software_field=software_field,
            first_n_tokens=first_n_tokens,
            organization=organization)
        cluster_number = int(list(kmeans.predict(pl.transform(data)))[0])
        db[config.SOFTWARE_COLLECTION].update({
            "_id": software['_id']
        }, {'$set': {
            cluster_field: cluster_number
        }})
        count += 1
        if count % 1000 == 0:
            print count
    print count


def create_training_data(software_field="Software Title",
                         first_n_tokens=10,
                         organization=False):
    softwares = db[config.SOFTWARE_COLLECTION].find()
    softwares = data_cleaner(
        softwares,
        software_field=software_field,
        first_n_tokens=first_n_tokens,
        organization=organization)
    return np.array(softwares)


def print_distribution_file():
    header = None
    f = open('datasets/distribution_file.csv', 'wb')
    cursor = db[config.SOFTWARE_COLLECTION].find()
    count = 0
    for software in cursor:
        del software['_id']
        if not header:
            header = software.keys()
            fw = csv.DictWriter(f, header)
            fw.writerow({k: k for k in header})
        fw.writerow({k: cnv(v) for k, v in software.items()})
        count += 1
        if count % 1000 == 0:
            print count
    print count
    f.close()


if __name__ == "__main__":
#     read_excel_and_move_data_in_mongo()
#     # CLuster Organizations
#     MODEL_FILE = "orgKMeans"
#     TFIDF_FILE = "orgTfIdfVector"
#     SOFTWARE_FIELD = "Publisher"
#     data = create_training_data(
#         software_field=SOFTWARE_FIELD, first_n_tokens=1, organization=True)
#     create_clusters(
#         data,
#         number_of_clusters=800,
#         model_file_name=MODEL_FILE,
#         tfidf_vector_file_name=TFIDF_FILE)
#     set_cluster_number(
#         software_field=SOFTWARE_FIELD,
#         cluster_field="publisherClusterNumber",
#         model_file_name=MODEL_FILE,
#         tfidf_vector_file_name=TFIDF_FILE,
#         first_n_tokens=1,
#         organization=True)
    # Cluster Softwares
    data = create_training_data(first_n_tokens=3)
    create_clusters(data, number_of_clusters=3000)
    set_cluster_number(first_n_tokens=3)
    print_distribution_file()
