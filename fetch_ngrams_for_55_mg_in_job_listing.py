from db_utils import DBUtils
from utils import find_all_ngrams_upto
import re

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
        n_grams = find_all_ngrams_upto(title, n=4)
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
        n_grams = find_all_ngrams_upto(title, n=4)
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


if __name__ == "__main__":
    print_ngram_stats()
    print "Done"
