from db_utils import DBUtils
import csv
import math

db_master = DBUtils(db_name='zippia', host='master.mongodb.d.int.zippia.com')
db_local = DBUtils(db_name='test', host='localhost')


def fetch_zero_time_paths(collection_name='careerPathsForMajors',
                          use_local_db=False):
    complete_zero = {}
    any_edge_zero = {}
    if use_local_db:
        cursor = db_local.fetch_data(collection_name)
    else:
        cursor = db_master.fetch_data(collection_name)
    for elem in cursor:
        major = elem['name']
        for degree in ["graduate", "under_graduate", "other"]:
            for path in elem[degree + '_paths']:
                all_zero = True
                has_zero_edge = False
                for node_obj in path[:-1]:
                    if node_obj['medianYrs'] and all_zero:
                        all_zero = False
                    elif not node_obj['medianYrs'] and not has_zero_edge:
                        if degree not in any_edge_zero:
                            any_edge_zero[degree] = {}
                        if major not in any_edge_zero[degree]:
                            any_edge_zero[degree][major] = 0
                        any_edge_zero[degree][major] += 1
                        has_zero_edge = True
                if all_zero:
                    if degree not in complete_zero:
                        complete_zero[degree] = {}
                    if major not in complete_zero[degree]:
                        complete_zero[degree][major] = 0
                    complete_zero[degree][major] += 1
    f = open('zero_time_paths.csv', 'wb')
    f.write("Major\tDegree\tAny_Edge_zero\tComplete_Path_Zero\n")
    for degree, major_path_dict in any_edge_zero.items():
        for major, count in major_path_dict.items():
            count2 = complete_zero[degree][major] if (
                degree in complete_zero and
                major in complete_zero[degree]) else 0
            f.write("{}\t{}\t{}\t{}\n".format(major, degree, count, count2))
    f.close()


def fetch_median_time_for_title():
    title_durations = {}
    f = open('title_time_file.csv', 'rb')
    fr = csv.reader(f, delimiter='\t')
    for row in fr:
        title = row[0]
        time_list = [float(t) for t in row[2:] if t]
        title_durations[title] = time_list
    return title_durations


def update_zero_time_paths(collection_name='careerPathsForMajors_dev'):
    title_durations = fetch_median_time_for_title()
    cursor = db_master.fetch_data('careerPathsForMajors')
    for elem in cursor:
        major = elem['name']
        has_zero_edge = False
        for degree in ["graduate", "under_graduate", "other"]:
            for path in elem[degree + '_paths']:
                for j, node_obj in enumerate(path[:-1]):
                    if not node_obj['medianYrs']:
                        title1 = node_obj['title']
                        title2 = path[j + 1]['title']
                        if (title1 in title_durations and
                                title2 in title_durations):
                            for t in title_durations[title1]:
                                node_obj['medianYrs'] = math.ceil(
                                    abs(t - title_durations[title2][0]))
                                if node_obj['medianYrs']:
                                    break
                            has_zero_edge = True

#         if has_zero_edge:
        print "updated major: {}".format(major)
        db_local.insert_records(collection_name, elem)


def test_sample_paths():
    f = open('zero_sample_paths.csv', 'wb')
    cursor = db_master.fetch_data('careerPathsForMajors')
    for elem in cursor:
        for degree in ["graduate", "under_graduate", "other"]:
            for i, path in enumerate(elem[degree + '_paths']):
                all_zero = True
                for node_obj in path[:-1]:
                    if node_obj['medianYrs'] and all_zero:
                        all_zero = False
                        break
                if all_zero:
                    e2 = db_local.fetch_data('careerPathsForMajors_dev',
                                             'cursor', {'_id': elem['_id']})[0]
                    time_list = []
                    for node_obj in e2[degree + "_paths"][i][:-1]:
                        time_list.append(node_obj['medianYrs'])
                    print elem['name'], degree, i, len(time_list), len(path)
                    path_time = sum(time_list) if time_list else 0
                    f.write("{}\t{}\t{}\t{}\n".format(elem[
                        'name'], degree, path_time, "\t".join([
                            "({},{})".format(n_o['title'], time_list[j])
                            if j < (len(path) - 1) else n_o['title']
                            for j, n_o in enumerate(path)
                        ])))
    f.close()


if __name__ == "__main__":
    #     fetch_zero_time_paths()
    collection_name = 'careerPathsForMajors_dev'
    update_zero_time_paths(collection_name)
    fetch_zero_time_paths(collection_name, use_local_db=True)
    #     test_sample_paths()
    print "done"
