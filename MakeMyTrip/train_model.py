# -*- coding: utf-8 -*-
import os
import random
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import SGDClassifier
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn import metrics
from sklearn.externals import joblib
import re
import csv


def rcnv(t):
    if t:
        t = "".join()
    return t


MODEL_PATH = 'dataset/'
MODEL_FILE_EXTENSION = '.pkl'

def save_to_file(filename, context, folder_path=MODEL_PATH):
    if folder_path.strip():
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        if folder_path.strip()[-1] != '/':
            folder_path = folder_path.strip() + "/"
    joblib.dump(context, folder_path + filename + "." +
                MODEL_FILE_EXTENSION)
    return (" file <{}> successfully saved".format(
        folder_path + filename + "." +
        MODEL_FILE_EXTENSION))


def load_file(filename, folder_path=MODEL_PATH):
    if folder_path.strip() and folder_path.strip()[-1] != '/':
        folder_path = folder_path.strip() + "/"
    return joblib.load(folder_path + filename + "." +
                       MODEL_FILE_EXTENSION)


def read_sample_data_set(training_file_path='dataset/train.csv', fraction=1.0):
    data = []
    f = open(training_file_path,'rb')
    fr = csv.DictReader(f)
    for row in fr:
        target = int(row['P'])
        del row['id']
        del row['P']
        data.append([row,target])
    random.shuffle(data)
    return_dict = {}
    return_dict['data'] = [x[0] for x in data[:int(len(data)*fraction)]]
    return_dict['targets'] = [x[1] for x in data[:int(len(data)*fraction)]]
    print "Done Data Reading"
    return return_dict

class DataCleaner:
    def __init__(self):
        self.pattern1 = re.compile("([ ]*\.[ ]*)+")
        self.pattern2 = re.compile(" +")
        self.headers = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"]
        pass

    def replace_special_tokens(self, data_dict):
        data = "|".join("{}_{}".format(h,data_dict[h]) for h in self.headers)
        return data

    def transform(self, data, y=None):
        result_data = []
        for d_t in data:
            d = self.replace_special_tokens(d_t)
            result_data.append(d)
        return result_data

    def fit(self, data, target):
        return self


def train_model():
    data_dict = read_sample_data_set(fraction=1.0)
    text_clf = Pipeline(
        [('preprocessor', DataCleaner()),
         ('vect', CountVectorizer(stop_words='english')),
         ('tfidf', TfidfTransformer()), 
         ('feature_section', TruncatedSVD(
             n_components=200,
             algorithm='randomized',
             n_iter=10,
             random_state=42)), 
         ('clf', SGDClassifier(loss="modified_huber"))])
    text_clf = text_clf.fit(data_dict['data'], data_dict['targets'])

    print save_to_file("Model", text_clf)


def test_model():
    text_clf = load_file("Model")
    test_data = read_sample_data_set(fraction=0.2)

    predicted = text_clf.predict(test_data['data'])
    print "Accuracy: {}%".format(
        np.mean(predicted == test_data['targets']) * 100)
#     print(metrics.classification_report(
#         test_data['targets'],
#         predicted,
#         target_names=list(set(test_data['targets']))))
    print metrics.confusion_matrix(test_data['targets'], predicted)
    f = open('dataset/mismatch_predictions.csv', 'wb')
    fw = csv.DictWriter(f, ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "Real", "Prediction"])
    mismatch_count = 0
    total_count = 0
    for i, prediction in enumerate(predicted):
        label = test_data['targets'][i]
        if label != prediction:
            mismatch_count += 1
            test_data['data'][i].update({"Real":label, "Prediction":prediction})
            fw.writerow(test_data['data'][i])
        total_count += 1
    f.close()
    print "Total Test Count: {}, Mismatch Count: {}".format(total_count,
                                                            mismatch_count)
    print "Done"


def read_test_data_set(file_path='dataset/test.csv', fraction=1.0):
    data = []
    f = open(file_path,'rb')
    fr = csv.DictReader(f)
    for row in fr:
        data.append(row)
    return data

def predict_results():
    text_clf = load_file("Model")
    test_data = read_test_data_set(fraction=1.0)
    predicted = text_clf.predict(test_data)
    
    f = open('dataset/predictions.csv', 'wb')
    fw = csv.DictWriter(f, ["id", "P"])
    fw.writerow({"id":"id", "P":"P"})
    total_count = 0
    for i, prediction in enumerate(predicted):
        fw.writerow({"id":test_data[i]["id"], "P":prediction})
        total_count += 1
    f.close()
    print "Done"


if __name__ == "__main__":
#     train_model()
#     test_model()
    predict_results()
