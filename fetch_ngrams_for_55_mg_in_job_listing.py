from db_utils import DBUtils
from utils import find_all_ngrams_upto
import re
import csv

db = DBUtils(db_name='JobListings', host='master.mongodb.d.int.zippia.com')

collection_name = db.fetch_data('MetaCollection')[0]['current']
major_group = 53


def print_ngrams_for_mg():
    cursor = db.fetch_data(
        collection_name, 'cursor',
        {'socCode': {
            '$regex': '^' + str(major_group) + '-'
        }}, {'titleDisplay': 1})
    n_gram_freq = {}
    count = 0
    for elem in cursor:
        title = elem['titleDisplay']
        title = re.sub("\W+", " ", title)
        n_grams = find_all_ngrams_upto(title.lower(), n=4)
        for ng in n_grams:
            if ng not in n_gram_freq:
                n_gram_freq[ng] = 0
            n_gram_freq[ng] += 1
        count += 1
        if count % 10000 == 0:
            print "{} entries processed".format(count)
    print "{} entries processed".format(count)

    #     f= open('all_ngrams.csv', 'wb')
    #     for ng, c in n_gram_freq.items():
    #         if c>=100:
    #             f.write("{}\t{}\n".format(ng, c))
    #     f.close()
    return dict([(ng, c) for ng, c in n_gram_freq.items() if c >= 100])


def print_ngram_stats():
    selected_ngrams = print_ngrams_for_mg()
    print "ngrams selection done"

    cursor = db.fetch_data(collection_name, 'cursor', {},
                           {'socCode': 1,
                            'titleDisplay': 1})
    n_gram_freq = {}
    count = 0
    for elem in cursor:
        mg = int(elem['socCode'][:2])
        if mg == major_group:
            continue
        title = elem['titleDisplay']
        title = re.sub("\W+", " ", title)
        n_grams = find_all_ngrams_upto(title.lower(), n=4)
        for ng in n_grams:
            if ng in selected_ngrams:
                if ng not in n_gram_freq:
                    n_gram_freq[ng] = {}
                    n_gram_freq[ng]['majors'] = set()
                    n_gram_freq[ng]['count'] = 0
                n_gram_freq[ng]['majors'].add(mg)
                n_gram_freq[ng]['count'] += 1
        count += 1
        if count % 10000 == 0:
            print "{} entries processed".format(count)
    print "{} entries processed".format(count)

    f = open('selected_ngrams.csv', 'wb')
    for ng, stats_dict in n_gram_freq.items():
        f.write("{}\t{}\t{}\t{}\n".format(ng, selected_ngrams[
            ng], len(stats_dict['majors']), stats_dict['count']))
    for ng, c in selected_ngrams.items():
        if ng not in n_gram_freq:
            f.write("{}\t{}\t{}\t{}\n".format(ng, c, 0, 0))
    f.close()


def read_csv_and_create_ngrams():
    f = open('/home/rohit/Desktop/selected_ngrams.csv', 'rb')
    fr = csv.reader(f, delimiter='\t')
    selected_entries = {}
    for row in fr:
        [title, count_53, overall_major_sum
         ] = [row[0], int(row[1]), int(row[3])]
        title = title.lower()
        if title not in selected_entries:
            selected_entries[title] = [0, 0]
        selected_entries[title][0] += count_53
        selected_entries[title][1] += overall_major_sum
    f.close()

    f = open('/home/rohit/Desktop/selected_ngrams_for_driver.csv', 'wb')
    for title, count_tuple in selected_entries.items():
        if (count_tuple[1] * 100) / count_tuple[0] < 5:
            f.write("{}\t{}\t{}\n".format(title, count_tuple[0], count_tuple[
                1]))
    f.close()


if __name__ == "__main__":
    #     print_ngram_stats()
    read_csv_and_create_ngrams()
    print "Done"
