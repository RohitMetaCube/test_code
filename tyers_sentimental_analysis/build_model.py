'''
Created on 01-Dec-2019

@author: rohit
'''
import csv
from collections import defaultdict
import re
import os
from sklearn.externals import joblib
import numpy as np
import nltk
from nltk.stem.porter import PorterStemmer
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import SGDClassifier
#from sklearn.ensemble import RandomForestClassifier
#from sklearn import metrics
from random import shuffle

ps = PorterStemmer()

MODEL_PATH = 'datasets/RF/'
MODEL_FILE_EXTENSION = "pkl"


def save_to_file(filename, context, folder_path=MODEL_PATH):
    if folder_path.strip():
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        if folder_path.strip()[-1] != '/':
            folder_path = folder_path.strip() + "/"
    joblib.dump(context, folder_path + filename + "." + MODEL_FILE_EXTENSION)
    return (" file <{}> successfully saved".format(folder_path + filename + "."
                                                   + MODEL_FILE_EXTENSION))


def load_file(filename, folder_path=MODEL_PATH):
    if folder_path.strip() and folder_path.strip()[-1] != '/':
        folder_path = folder_path.strip() + "/"
    return joblib.load(folder_path + filename + "." + MODEL_FILE_EXTENSION)


def read_data(file_path='datasets/Evaluation-dataset.csv'):
    f = open(file_path, "rb")
    fr = csv.reader(f)
    dataset = defaultdict(list)
    for row in fr:
        text = row[0]
        labels = row[1:]
        for l in labels:
            #             if l:
            #                 sentiment = l[l.rfind(' ')+1:]
            #                 l = l[:l.rfind(' ')]
            #                 dataset[(l, sentiment)].append(text)
            dataset[l].append(text)
    return dataset


def train_test_split(data, targets, test_size):
    md = zip(data, targets)
    shuffle(md)
    data, targets = [k[0] for k in md], [k[1] for k in md]
    test_size = int(len(data) * test_size)
    print "Test Size", test_size
    X_train, X_test, y_train, y_test = data[:-test_size], data[
        -test_size:], targets[:-test_size], targets[-test_size:]
    return X_train, X_test, y_train, y_test


def create_sample_data_set(test_fraction=0.2):
    data = []
    targets = []
    dataset = read_data()
    for label in dataset:
        texts = dataset[label]
        for text in texts:
            data.append(text)
            targets.append(label)
        print "Done Label: {}".format(label)
    X_train, X_test, y_train, y_test = train_test_split(
        data, targets, test_size=test_fraction)
    return_object = {}
    return_object['data'] = X_train
    return_object['targets'] = y_train
    return_object['test_data'] = X_test
    return_object['test_targets'] = y_test
    return return_object


def ngrams(tokens, n):
    output = []
    for i in range(len(tokens) - n + 1):
        output.append(tokens[i:i + n])
    return output


def tokenize_sentence(sentences, extra_split=False):
    sentences = re.sub('[^a-zA-Z]', ' ', sentences.lower())
    new_sentences = nltk.sent_tokenize(sentences)
    tokens = []
    for sentence in new_sentences:
        sentence_tokens = nltk.word_tokenize(sentence)
        bigrams = ngrams(sentence_tokens, 2)
        trigrams = ngrams(sentence_tokens, 3)
        tokens.extend(sentence_tokens)
        for b in bigrams:
            tokens.append(b[0] + " " + b[1])
        for t in trigrams:
            tokens.append(t[0] + " " + t[1] + " " + t[2])
    return tokens


def train_model(data_dict):
    text_clf = Pipeline([
        ('vect', CountVectorizer(
            tokenizer=tokenize_sentence,
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 3),
            binary=True,
            max_features=100)), ('tfidf', TfidfTransformer()),
        ('clf', SGDClassifier(loss="modified_huber"))
        #('clf', RandomForestClassifier(
        #    n_estimators=501, criterion='entropy'))
    ])
    text_clf = text_clf.fit(data_dict['data'], data_dict['targets'])

    print save_to_file("Model", text_clf)


def test_model(data_dict):
    text_clf = load_file("Model")
    predicted = text_clf.predict(data_dict['test_data'])
    print "Accuracy: {}%".format(
        np.mean(predicted == data_dict['test_targets']) * 100)
    #     print(metrics.classification_report(
    #         data_dict['test_targets'],
    #         predicted,
    #         target_names=list(set(data_dict['test_targets']))))
    #     print metrics.confusion_matrix(data_dict['test_targets'], predicted)
    #     mismatch_count = 0
    #     total_count = 0
    #     for i, prediction in enumerate(predicted):
    #         label = data_dict['test_targets'][i]
    #         if label != prediction:
    #             mismatch_count += 1
    #         total_count += 1
    #     print "Total Test Count: {}, Mismatch Count: {}".format(total_count,
    #                                                             mismatch_count)
    print "Done"


def build_and_test():
    data_dict = create_sample_data_set(test_fraction=0.1)
    train_model(data_dict)
    test_model(data_dict)


if __name__ == "__main__":
    build_and_test()
