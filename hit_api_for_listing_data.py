from db_utils import DBUtils
from configurator import configurator
import requests
import time
from utils import cnv
import re


def rcnv(t):
    t = cnv(t)
    if not t:
        t = ""
    return t


def normalization_function(
        input_array,
        api='job',
        array='jobs',
        server=configurator.commons.JOB_NORMALIZATION_API_HOST,
        port=configurator.commons.JOB_NORMALIZATION_API_PORT):
    link = "http://" + server + ":" + str(port) + "/" + api + "/normalize"
    data = {array: input_array}
    r = requests.post(link, json=data)
    return r.json()


def read_driver_ngrams():
    ngrams = set(['cdl', 'otr', 'truck', 'driving', 'uber', 'tanker', 'lyft'])
    return ngrams


def read_test_data(db, limit=1000, collection_name='JobCollection1'):
    driver_ngrams = read_driver_ngrams()
    cursor = db.fetch_data(collection_name, 'cursor', {},
                           {'socCode': 1,
                            'titleDisplay': 1,
                            'desc': 1})
    jobs = {}
    jobs['data_array'] = []
    jobs['ids'] = []
    jobs['soc_codes'] = []
    jobs['titles'] = {}
    count1 = 0
    count2 = 0
    count = 0
    for elem in cursor:
        title = "titleDisplay"
        soc_code = 'socCode'
        desc = 'desc'

        count += 1
        if count % 10000 == 0:
            print "{} entries done with count1:{} and count2:{}".format(
                count, count1, count2)

        if ((elem[title] and elem[title].strip() and
             elem[title].strip().lower() not in set(["null", "none"]))):
            #             or (
            #              elem[desc] and elem[desc].strip() and 
            #              elem[title].strip().lower() not in set(["null", "none"]))):

            new_entry = {}
            new_entry['title'] = rcnv(elem[title]) if elem[title] else ""
            new_entry['description'] = rcnv(elem[desc]) if elem[desc] else ""

            t = elem[title].lower()
            t = re.sub("\W+", ' ', t)
            t_ngrams = set(t.split())  #find_all_ngrams_upto(t, 4)
            if t_ngrams.intersection(driver_ngrams) and elem[
                    soc_code][:2] != "53":
                if count1 < limit:
                    if new_entry['title'] not in jobs['titles']:
                        jobs['titles'][new_entry['title']] = 1
                        count1 += 1
                    else:
                        jobs['titles'][new_entry['title']] += 1
                        continue
                else:
                    continue
            else:
                if count2 < limit:
                    if new_entry['title'] not in jobs['titles']:
                        jobs['titles'][new_entry['title']] = 1
                        count2 += 1
                    else:
                        jobs['titles'][new_entry['title']] += 1
                        continue
                else:
                    continue

            jobs['data_array'].append(new_entry)
            jobs['ids'].append(elem['_id'])
            jobs['soc_codes'].append(elem[soc_code])
            if count1 >= limit and count2 >= limit:
                break
    print "{} entries done with count1:{} and count2:{}".format(count, count1,
                                                                count2)
    return jobs


def update_jobs(db, jobs, collection_name, server):
    f = open('hit_result_file.csv', 'wb')
    f.write("ID\tTitle\tOld_Soc_code\tNew_Soc_code\n")
    start_index = 0
    end_index = 300
    total_entries = len(jobs['data_array']) + 300
    while end_index < total_entries:
        try:
            results = normalization_function(
                jobs['data_array'][start_index:end_index],
                api='job',
                array='jobs',
                server=server,
                port=configurator.commons.JOB_NORMALIZATION_API_PORT)[
                    'normalized_jobs']
            for j, res_node in enumerate(results):
                i = j + start_index
                new_soc = res_node['soc_code']
                old_soc = jobs['soc_codes'][i]
                _id = jobs['ids'][i]
                title = jobs['data_array'][i]['title']
                count = jobs['titles'][title]
                f.write("{}\t{}\t{}\t{}\t{}\n".format(_id, title, count,
                                                      old_soc, new_soc))
        except Exception as e:
            print e
        print "done {}/{}".format(end_index, total_entries - 300)
        start_index = end_index
        end_index += 300
    f.close()


def parallel_function(server):
    db = DBUtils(
        db_name='JobListings',
        host='master.mongodb.d.int.zippia.com',
        connect=False)
    collection_name = db.fetch_data('MetaCollection')[0]['current']
    hit_time = time.time()
    jobs = read_test_data(db, collection_name=collection_name)
    update_jobs(db, jobs, collection_name, server)
    print "{} hit time {}s".format('job', time.time() - hit_time)
    del jobs
    del db


if __name__ == '__main__':
    server = 'localhost'  #configurator.commons.JOB_NORMALIZATION_API_HOST
    total_time = time.time()
    parallel_function(server)
    print "total time to normalized resumes {}s".format(time.time() -
                                                        total_time)
    print "*****************) DONE (************"
