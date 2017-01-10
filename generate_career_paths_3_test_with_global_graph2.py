'''
THIS IS FINAL VERSION FOR 9 JANUARY 2017 (VERIFIED FOR "Economics" and "Biology")
1. Now we have local edges with global edges for any major nodes
2. we multiply local edge weight with a factor to be in a comparison of global edges
'''

import networkx as nx
from db_utils import DBUtils
import csv
import time
import re
import numpy as np
from configurator import configurator
import utils
from filter_chain import remove_stop_words
from sklearn.externals import joblib

dbutils = DBUtils(db_name='zippia', host='master.mongodb.d.int.zippia.com')
db_local = DBUtils(db_name='test', host='localhost')
db_zippia2 = DBUtils(db_name='zippia2', host='localhost')


def format_date(date_string):
    date_string = re.sub("\W+", " ", date_string.lower())
    date_string = re.sub("\d+[ ]*((year)|(yr))([s]{0,1})", " ", date_string)
    date_string = re.sub("\d+[ ]*((month)|(mt))([s]{0,1})", " ", date_string)
    date_string = re.sub(" +", " ", date_string).strip()
    return date_string


class valid_edge_checker:
    level_dict = {
        "Lead": set([
            "Senior", "Vice", "Junior", "Trainee", "Fellow", "Associate",
            "Adjunct", "Assistant"
        ]),
        "Leader": set([
            "Senior", "Vice", "Junior", "Trainee", "Fellow", "Associate",
            "Adjunct", "Assistant"
        ]),
        "Senior": set([
            "Vice", "Junior", "Trainee", "Fellow", "Associate", "Adjunct",
            "Assistant"
        ]),
        "Principal": set([
            "Lead", "Head", "Senior", "Vice", "Junior", "Trainee", "Fellow",
            "Associate", "Adjunct", "Assistant"
        ]),
        "Chief": set([
            "Lead", "Head", "Senior", "Vice", "Junior", "Trainee", "Fellow",
            "Associate", "Adjunct", "Assistant"
        ]),
        "Head": set([
            "Senior", "Vice", "Junior", "Trainee", "Fellow", "Associate",
            "Adjunct", "Assistant"
        ]),
        "Deputy": set([
            "Lead", "Head", "Senior", "Vice", "Junior", "Trainee", "Fellow",
            "Associate", "Adjunct", "Assistant"
        ]),
        "Adjunct": set(["Trainee", "Fellow", "Associate", "Assistant"]),
        "Associate": set(["Trainee", "Fellow", "Assistant"]),
        "Assistant": set(["Trainee", "Fellow"]),
        "Junior": set(["Trainee", "Fellow"])
    }

    level_words = {
        "Volunteer": -5,
        "Intern": -5,
        "Internship": -5,
        "Extern": -5,
        "Externship": -5,
        "Junior": -4,
        "Assistant": -3,
        "Associate": -2,
        "Adjunct": -1,
        "Vice": -1,
        "Senior": 1,
        "Staff": 2,
        "Principal": 3,
        "Supervisor": 4,
        "Lead": 4,
        "Leader": 4,
        "Head": 4,
        "Architect": 5,
        "Manager": 6,
        "Dean": 7,
        "Director": 8,
        "Executive": 8,
        'Administrator': 8,
        "President": 9,
        "Chancellor": 10,
        "Chief": 10,
    }

    @staticmethod
    def is_valid_edge(node1, node2):
        node1_tokens = remove_stop_words.apply(re.sub("\W+", " ",
                                                      node1)).split()
        node2_tokens = remove_stop_words.apply(re.sub("\W+", " ",
                                                      node2)).split()
        node2_ngrams = utils.find_ngrams(node2_tokens, 2, separator=" ")
        node2_tokens = set(node2_tokens)
        node2_ngrams.update(node2_tokens)
        node1_ngrams = utils.find_ngrams(node1_tokens, 2, separator=" ")
        node1_tokens = set(node1_tokens)
        node1_ngrams.update(node1_tokens)
        diff1 = list(node1_tokens.difference(node2_tokens))
        diff2 = list(node2_tokens.difference(node1_tokens))
        valid_flag = True
        if (((len(node1_tokens) - len(node2_tokens)) == 1 and
             len(node1_tokens.intersection(node2_tokens)) == len(node2_tokens)
             and diff1[0] in set([
                 "Lead", "Leader", "Senior", "Principal", "Chief", "Head",
                 "Deputy"
             ])) or
            ((len(node2_tokens) - len(node1_tokens)) == 1 and
             len(node1_tokens.intersection(node2_tokens)) == len(node1_tokens)
             and diff2[0] in set([
                 "Vice", "Junior", "Trainee", "Fellow", "Associate", "Adjunct",
                 "Assistant"
             ])) or (node2_ngrams.intersection([
                 "Internship", "Externship", "Volunteer", "Intern", "Extern",
                 "Student", "Customer Service", "Cashier", "Server",
                 "Bartender", 'Insurance Agent', "Research Assistant",
                 "Teaching Assistant", "Graduate Assistant",
                 "Administrative Assistant", "Receptionist"
             ]))):
            valid_flag = False
        elif len(diff1) == 1 and len(diff2) == 1 and (
                diff1[0] in valid_edge_checker.level_dict and
                diff2[0] in valid_edge_checker.level_dict[diff1[0]]):
            valid_flag = False
        elif (node1_tokens.intersection([
                "Manager", "Director", "Engineer", "Principal", "President",
                "Scientist", "Chief", "Chancellor", "Deputy"
        ]) and node2 in set([
                "Sales", "Sales Representative", "Sales Associate", "Server",
                "Coordinator", "Pharmacist Technician"
        ])):
            valid_flag = False
        elif node2 in set([
                "Sales", "Sales Representative", "Sales Associate", "Server",
                "Coordinator"
        ]):
            valid_flag = False
        else:
            levels1 = [
                valid_edge_checker.level_words[t1] for t1 in diff1
                if t1 in valid_edge_checker.level_words
            ]
            levels2 = [
                valid_edge_checker.level_words[t2] for t2 in diff2
                if t2 in valid_edge_checker.level_words
            ]
            level1 = max(levels1) if levels1 else 0
            level2 = max(levels2) if levels2 else 0
            if node1_tokens.intersection(node2_tokens) and level1 > level2:
                valid_flag = False
        return valid_flag


def remove_edges(edges, start_titles, end_titles, edge_count_threshold=3):
    print "Removing reverse edges..."
    edge_count = 0
    valid_edges = {}
    for edge in edges:
        reverse_edge = (edge[1], edge[0])
        if valid_edge_checker.is_valid_edge(
                edge[0],
                edge[1]) and edges[edge]['count'] >= edge_count_threshold:
            if reverse_edge in edges:
                if (not valid_edge_checker.is_valid_edge(edge[1], edge[0])
                    ) or (edges[edge]['count'] >= edges[reverse_edge]['count']
                          and reverse_edge not in valid_edges):
                    valid_edges[edge] = edges[edge]['count']
            else:
                valid_edges[edge] = edges[edge]['count']
            if edge[0] in start_titles and edge[
                    1] in end_titles and edge in valid_edges:
                valid_edges[edge] = valid_edges[edge] / 10 if valid_edges[
                    edge] > 10 else 0.1
        edge_count += 1
        if edge_count % 100000 == 0:
            print "{} edges processed.".format(edge_count)
    print "Removed reverse edges..."
    return valid_edges


def read_global_frequent_transitions():
    edges = {}
    f = open('frequent_transitions_all_edges.csv', 'rb')
    fr = csv.reader(f, delimiter='\t')
    for row in fr:
        from_title = row[0]
        to_title = row[1]
        freq = int(row[2])
        edge = (from_title, to_title)
        edges[edge] = freq
    f.close()
    return edges


global_edges = read_global_frequent_transitions()


def manage_edges(edge_dict, resume_count, depriotize_starts):
    if resume_count <= 3000:
        threshold = 5
    elif resume_count <= 20000:
        threshold = 50
    else:
        threshold = 100
#     global_weights= {}
    new_degree_edges = {}
    all_nodes = set()
    for edge in edge_dict:
        all_nodes.add(edge[0])
        all_nodes.add(edge[1])
    all_nodes = list(all_nodes)
    for i, n1 in enumerate(all_nodes):
        for n2 in all_nodes[i + 1:]:
            node1 = n1
            node2 = n2
            if (((n1, n2) not in global_edges and (n2, n1) in global_edges) or
                ((n1, n2) in global_edges and (n2, n1) in global_edges and
                 global_edges[(n2, n1)] > global_edges[(n1, n2)])):
                node1 = n2
                node2 = n1

            if (((node1, node2) in global_edges and
                 global_edges[(node1, node2)] >= threshold) or
                ((node1, node2) in edge_dict and
                 (edge_dict[(node1, node2)]['count'] * 10) >= threshold)):
                new_degree_edges[(node1, node2)] = {}
                new_degree_edges[(node1, node2)]['count'] = global_edges[(
                    node1, node2)] if (node1, node2) in global_edges else 0
                if (node1, node2) in edge_dict:
                    new_degree_edges[(node1, node2)]['count'] += edge_dict[(
                        node1, node2)]['count'] * 10
                if node1 in depriotize_starts or set(
                        re.sub("\W+", " ", node1).split()).intersection(
                            ["Sales"]):
                    new_degree_edges[(node1, node2)]['count'] = float(
                        new_degree_edges[(node1, node2)]['count']) / 10
                new_degree_edges[(node1, node2)]['time_intervals'] = []
                if (node1, node2) in edge_dict:
                    new_degree_edges[(node1, node2)]['time_intervals'].extend(
                        edge_dict[(node1, node2)]['time_intervals'])
                elif (node2, node1) in edge_dict:
                    new_degree_edges[(node1, node2)]['time_intervals'].extend(
                        edge_dict[(node2, node1)]['time_intervals'])

#                 if (node1, node2) not in global_weights:
#                     global_weights[(node1, node2)]= []
#                 global_weights[(node1, node2)].extend(new_degree_edges[(node1, node2)]['time_intervals'])
    return new_degree_edges


def create_graph_for_majors(major, degrees, work_meta_info, min_conf,
                            depriotize_starts):
    edges = {}
    nodes = set()
    resume_count = 0
    resumes = dbutils.fetch_data(
        'resume', "cursor",
        {'latest_ed_major': major,
         'latest_ed_degree': {
             '$in': list(degrees)
         }})
    for resume in resumes:
        ''' Look at the last education info '''
        resume_count += 1
        create_edges_from_resume(resume, work_meta_info, min_conf, edges,
                                 nodes, resume["latest_ed_major"])
        if resume_count % 10000 == 0:
            print "Processed {} resumes".format(resume_count)
    print "Statistics for major:", major

    edges = manage_edges(edges, resume_count, depriotize_starts)
    print "The graph has: {} edges and {} nodes".format(len(edges), len(nodes))
    return edges


def create_graph(edges, sts, ets, edge_count_threshold):
    career_graph = nx.DiGraph()
    valid_edges = remove_edges(
        edges, sts, ets, edge_count_threshold=edge_count_threshold)
    print "length of valid edges", len(valid_edges)
    edge_list = []
    for edge in valid_edges:
        weight = 1.0 / (1.0 * valid_edges[edge])
        edge_list.append((edge[0], edge[1], weight))
    career_graph.add_weighted_edges_from(edge_list)
    return career_graph


def create_edges_from_resume(resume, work_meta_info, min_conf, edges, nodes,
                             major):
    is_valid_date_flag = True
    [d, m, y] = [
        int(x)
        for x in extract_from_date(resume["latest_ed_from"], resume[
            "latest_ed_to"]).split(',')
    ]
    if y == 100000 or not y:
        is_valid_date_flag = False

    if is_valid_date_flag:
        valid_index = False
        path = []
        title_time_map = {}
        for index in reversed(range(1, 15)):
            current_work_ex_meta_info = work_meta_info[index]
            next_work_ex_meta_info = work_meta_info[index - 1]
            if (current_work_ex_meta_info["title"] in resume and
                    resume[current_work_ex_meta_info["title"]] and
                    current_work_ex_meta_info["match"] in resume and
                    resume[current_work_ex_meta_info["match"]] and
                    current_work_ex_meta_info["confidence"] in resume and
                    resume[current_work_ex_meta_info["confidence"]] >= min_conf
                    and next_work_ex_meta_info["title"] in resume and
                    resume[next_work_ex_meta_info["title"]] and
                    next_work_ex_meta_info["match"] in resume and
                    resume[next_work_ex_meta_info["match"]] and
                    next_work_ex_meta_info["confidence"] in resume and
                    resume[next_work_ex_meta_info["confidence"]] >= min_conf
                    and resume[current_work_ex_meta_info["title"]] !=
                    resume[next_work_ex_meta_info["title"]]):
                ''' There is a valid edge present from the work experience at index to the one 
                at (index-1) '''
                current_date = extract_from_date(
                    resume[current_work_ex_meta_info['from']],
                    resume[current_work_ex_meta_info['to']])
                [cd, cm, cy] = [int(x) for x in current_date.split(',')]
                if valid_index or (d + m * 30 + y * 365) <= (
                        cd + cm * 30 + cy * 365):
                    from_title = resume[current_work_ex_meta_info["title"]]
                    to_title = resume[next_work_ex_meta_info["title"]]
                    if not valid_index:
                        valid_index = True
                        path.append(from_title)
                        title_time_map[from_title] = current_date
                    path.append(to_title)
                    edge = (from_title, to_title)
                    if edge not in edges:
                        edges[edge] = {}
                        edges[edge]['count'] = 0
                        edges[edge]['time_intervals'] = []
                    if from_title not in nodes:
                        nodes.add(from_title)
                    if to_title not in nodes:
                        nodes.add(to_title)
                    edges[edge]['count'] += 1
                    next_date = extract_from_date(
                        resume[next_work_ex_meta_info['from']],
                        resume[next_work_ex_meta_info['to']])
                    title_time_map[to_title] = next_date
                    [issue_flag, date_diff] = utils.date_difference(
                        current_date, next_date)
                    if not issue_flag:
                        edges[edge]['time_intervals'].append(date_diff)
        for i, node1 in enumerate(path):
            current_date = title_time_map[
                node1] if node1 in title_time_map else ''
            for j, node2 in enumerate(path[i + 2:]):
                edge = (node1, node2)
                if edge not in edges:
                    edges[edge] = {}
                    edges[edge]['count'] = 0
                    edges[edge]['time_intervals'] = []
                edges[edge]['count'] += 1 / (j + 2)
                next_date = title_time_map[
                    node2] if node2 in title_time_map else ''
                if current_date and next_date:
                    [issue_flag, date_diff] = utils.date_difference(
                        current_date, next_date)
                    if not issue_flag:
                        edges[edge]['time_intervals'].append(date_diff)


def extract_from_date(from_date_string, to_date_string):
    current_date = format_date(from_date_string)
    d, m, y = utils.formatted_date(current_date)
    if y == 100000:
        current_date = format_date(to_date_string)
        d, m, y = utils.formatted_date(current_date)
    elif not y:
        [issue_flag, date_diff] = utils.date_difference(from_date_string,
                                                        to_date_string)
        if not issue_flag:
            last_date = format_date(to_date_string)
            ld, lm, ly = utils.formatted_date(last_date)
            if ly and ly != 100000:
                to_date = ld + lm * 30 + ly * 365 - date_diff
                d, m, y = int((to_date % 365) % 12), int(
                    (to_date % 365) / 12), int(to_date / 365)
    return "{},{},{}".format(d, m, y)


def read_start_titles_and_end_titles(top_k_start=15,
                                     top_k_end=15,
                                     depriotize_starts=set()):
    major_title_dict = {}
    f = open("Start_Titles_15_dec_2016.csv", 'rb')
    fr = csv.reader(f, delimiter="\t")
    for row in fr:
        major = row[0]
        degree = row[1]
        norm_degree_value = degree
        if major not in major_title_dict:
            major_title_dict[major] = {}
            major_title_dict[major]['start_titles'] = {}
            major_title_dict[major]['end_titles'] = {}
        if norm_degree_value not in major_title_dict[major]['start_titles']:
            major_title_dict[major]['start_titles'][norm_degree_value] = []
            major_title_dict[major]['end_titles'][norm_degree_value] = []
        major_title_dict[major]['start_titles'][norm_degree_value] = []
        s_count = 0
        depriortize_set = []
        for title_tuple in row[3:]:
            s_t = re.sub(",\d+\)", "", title_tuple[1:])
            if major == "Computer Science" and s_t == "Network Administrator":
                depriortize_set.append(s_t)
            elif (s_t not in depriotize_starts and not set(
                ['Sales']).intersection(re.sub("\W+", " ", s_t).split())):
                major_title_dict[major]['start_titles'][
                    norm_degree_value].append(s_t)
                s_count += 1
            else:
                depriortize_set.append(s_t)
            if s_count >= top_k_start:
                break
        if s_count < top_k_start:
            for s_t in depriortize_set:
                major_title_dict[major]['start_titles'][
                    norm_degree_value].append(s_t)
    f.close()

    f = open("End_Titles_with_exp_and_W1_both.csv", 'rb')
    fr = csv.reader(f, delimiter="\t")
    for row in fr:
        major = row[0]
        degree = row[1]
        norm_degree_value = degree
        if major not in major_title_dict:
            major_title_dict[major] = {}
            major_title_dict[major]['start_titles'] = {}
            major_title_dict[major]['end_titles'] = {}
        if norm_degree_value not in major_title_dict[major]['end_titles']:
            major_title_dict[major]['start_titles'][norm_degree_value] = []
            major_title_dict[major]['end_titles'][norm_degree_value] = []
        s_count = 0
        depriortize_set = []
        for title_tuple in row[3:]:
            s_t = re.sub(",\d+\)", "", title_tuple[1:])
            if major == "Biology" and s_t in set([
                    "Quality Engineer", "Quality Manager",
                    "Quality Assurance Manager", "Production Manager"
            ]):
                depriortize_set.append(s_t)
            else:
                major_title_dict[major]['end_titles'][
                    norm_degree_value].append(s_t)
                s_count += 1
            if s_count >= top_k_end:
                break
        if s_count < top_k_end:
            for s_t in depriortize_set:
                major_title_dict[major]['end_titles'][
                    norm_degree_value].append(s_t)

    f.close()
    for major, degree_dict in major_title_dict.items():
        for degree, titles in degree_dict['end_titles'].items():
            if not titles or not degree_dict['start_titles'][degree]:
                del degree_dict['start_titles'][degree]
                del degree_dict['end_titles'][degree]
        if not degree_dict['start_titles'] or not degree_dict['end_titles']:
            del major_title_dict[major]
    return major_title_dict


def similarity_computer(array1, array2):
    intersection_count = len(set(array1).intersection(array2))
    return float((1 + intersection_count)) / len(array1)


def select_best_nodes(path, edge_weights, is_local_edge_dict=True):
    if len(path) > 4:
        start_node = path[0]
        end_node = path[-1]
        best_path = [start_node, end_node]
        best_path_weight = 0
        min_freq = 0
        for i, node1 in enumerate(path[1:-1]):
            for node2 in path[i + 1:-1]:
                l = len(set([start_node, node1, node2, end_node]))
                if is_local_edge_dict:
                    edge1_weight = edge_weights[(
                        start_node, node1)]['count'] if (
                            start_node, node1) in edge_weights else 0
                    edge2_weight = edge_weights[(node1, node2)]['count'] if (
                        node1, node2) in edge_weights else 0
                    edge3_weight = edge_weights[(
                        node2, end_node)]['count'] if (node2, end_node
                                                       ) in edge_weights else 0
                else:
                    edge1_weight = edge_weights[(start_node, node1)] if (
                        start_node, node1) in edge_weights else 0
                    edge2_weight = edge_weights[(
                        node1, node2)] if (node1, node2) in edge_weights else 0
                    edge3_weight = edge_weights[(node2, end_node)] if (
                        node2, end_node) in edge_weights else 0
                if l == 4:
                    if (min([edge1_weight, edge2_weight, edge3_weight]) >
                            min_freq or
                        (min([edge1_weight, edge2_weight, edge3_weight]) ==
                         min_freq and
                         sum([edge1_weight, edge2_weight, edge3_weight]) >=
                         best_path_weight)):
                        best_path_weight = sum(
                            [edge1_weight, edge2_weight, edge3_weight])
                        min_freq = min(
                            [edge1_weight, edge2_weight, edge3_weight])
                        best_path = [start_node, node1, node2, end_node]
                elif l == 3 and node1 == node2 and (
                        min([edge1_weight, edge3_weight]) > min_freq and
                        sum([edge1_weight, edge3_weight]) >= best_path_weight):
                    best_path_weight = sum([edge1_weight, edge3_weight])
                    best_path = [start_node, node1, end_node]

    else:
        best_path = path
    return best_path


def support_calculation(top_k_start, top_k_end, end_titles, start_titles,
                        degree_graph, major, degree, edges, title_time_dict):
    selected_paths = []
    rejected_paths = []
    len_frac = {4: 1, 3: 0.9, 2: 0.8}
    for end_index, et in enumerate(end_titles[:top_k_end]):
        all_paths = []
        for st in start_titles[:top_k_start]:
            if st != et:
                try:
                    new_paths = nx.all_simple_paths(
                        degree_graph, st, et, cutoff=3)
                    c = 0
                    for new_path in new_paths:
                        c += 1
                        l = len(new_path)
                        if l > 1:
                            if l > 4:
                                l = 4
                            new_path2 = select_best_nodes(
                                new_path, edges, is_local_edge_dict=True)
                            all_paths.append([new_path2, l])
                            for i, node1 in enumerate(new_path2[:-1]):
                                node2 = new_path2[i + 1]
                                if (node1, node2) not in edges:
                                    median_time = 0
                                    start_index = new_path.index(node1)
                                    end_index = new_path.index(node2)
                                    for j, node3 in enumerate(new_path[
                                            start_index:end_index]):
                                        node4 = new_path[start_index + j + 1]
                                        if (node3, node4) not in edges:
                                            median_time = abs(
                                                title_time_dict[node4] -
                                                title_time_dict[node3]) if (
                                                    node3 in title_time_dict
                                                    and node4 in
                                                    title_time_dict) else ''
                                            if not median_time:
                                                break
                                        if not edges[(node3, node4
                                                      )]['time_intervals']:
                                            median_time = abs(
                                                title_time_dict[node4] -
                                                title_time_dict[node3]) if (
                                                    node3 in title_time_dict
                                                    and node4 in
                                                    title_time_dict) else ''
                                            if not median_time:
                                                break
                                        median_time += np.median(edges[(
                                            node3, node4)]['time_intervals'])
                                    if median_time:
                                        edges[(node1, node2)] = {}
                                        edges[(node1, node2)]['count'] = 1
                                        edges[(
                                            node1, node2
                                        )]['time_intervals'] = [median_time]
                except:
                    pass
        for i, path in enumerate(all_paths):
            similarities = []
            for selected_path in selected_paths:
                similarity = similarity_computer(path[0], selected_path)
                similarities.append(similarity)
            if similarities:
                similarity = 1 / max(similarities)
            else:
                similarity = 4
            all_paths[i].append(similarity)
            all_weights = [(edges[(path[0][j - 1], node)]['count']
                            if (path[0][j - 1], node) in edges else 0)
                           for j, node in enumerate(path[0]) if j]
            all_weights = sorted(all_weights)
            all_paths[i].append(all_weights[0] * len_frac[path[1]] *
                                similarity)
            if len(all_weights) > 1:
                all_paths[i].append(all_weights[1] * len_frac[path[1]] *
                                    similarity)
            else:
                all_paths[i].append(0)
            if len(all_weights) > 2:
                all_paths[i].append(all_weights[2] * len_frac[path[1]] *
                                    similarity)
            else:
                all_paths[i].append(0)
            del all_weights
        try:
            all_paths = sorted(
                all_paths, key=lambda k: (k[3], k[4], k[5]), reverse=True)
            best_path = all_paths[0][0]
            selected_paths.append(best_path)
        except:
            pass
        if len(selected_paths) == 15:
            break
    sl = len(selected_paths)
    if sl < 15:
        rejected_paths = sorted(
            rejected_paths, key=lambda k: (k[3], k[4], k[5]), reverse=True)
        for path_tuple in rejected_paths[:(15 - sl)]:
            selected_paths.append(path_tuple[0])
        print "major: {}, degree: {}, clear_selected_paths: {}, after_adding_from rejected: {}".format(
            major, degree, sl, len(selected_paths))
    for p in selected_paths:
        print p
    return selected_paths


def print_paths_iterator(
        major,
        titles_dict,
        title_skills,
        required_skills_threshold,
        career_graph,
        edges,
        title_time_dict,
        iterate_on_degrees=["Graduate", "Under Graduate", "Other"]):
    result_paths = {}
    result_paths['graduate_paths'] = []
    result_paths['under_graduate_paths'] = []
    result_paths['other_paths'] = []
    for degree, end_titles in titles_dict["end_titles"].items():
        start_titles = titles_dict["start_titles"][degree]
        selected_paths = support_calculation(30, 50, end_titles, start_titles,
                                             career_graph, major, degree,
                                             edges, title_time_dict)

        path_index = 1
        k = "_".join(degree.lower().split()) + "_paths"
        for selected_path in selected_paths:
            new_path = []
            best_path = selected_path  #select_best_nodes(selected_path, edges)
            for node_index, title in enumerate(best_path[:-1]):
                edge = (title, best_path[node_index + 1])
                current_skills = set(title_skills[title][
                    'skill_set']) if title in title_skills else set([])
                next_skills = title_skills[best_path[node_index + 1]][
                    'skill_set'] if best_path[node_index +
                                              1] in title_skills else []
                new_obj = {}
                new_obj['title'] = title
                new_obj['socCode'] = title_skills[title][
                    'soc_code'] if title in title_skills else ""
                if edge in edges:
                    new_obj['medianYrs'] = np.median(edges[edge][
                        'time_intervals']) if edges[edge][
                            'time_intervals'] else ""
                else:
                    new_obj['medianYrs'] = abs(title_time_dict[edge[
                        1]] - title_time_dict[edge[0]]) if (
                            edge[0] in title_time_dict and
                            edge[1] in title_time_dict) else ""
                new_obj['skills'] = []
                new_skills_count = 0
                for skill in next_skills:
                    if skill not in current_skills:
                        new_obj['skills'].append(skill)
                        new_skills_count += 1
                    if new_skills_count >= required_skills_threshold:
                        break
                new_path.append(new_obj)
            new_obj = {}
            new_obj['title'] = best_path[-1]
            new_obj['socCode'] = title_skills[title][
                'soc_code'] if title in title_skills else ""
            new_path.append(new_obj)
            if len(new_path) > 1:
                result_paths[k].append(new_path)
            path_index += 1
    return [result_paths, edges]


def append_new_paths(result_paths,
                     edge_weights,
                     final_valid_paths,
                     path_name='graduate_paths'):
    len_frac = {4: 1, 3: 0.9, 2: 0.8}
    all_paths = []
    path_obj = {}
    for path in result_paths[path_name]:
        grad_path = [node_obj['title'] for node_obj in path]
        all_paths.append(grad_path)
        key = "_".join(grad_path)
        path_obj[key] = path
    selected_paths = []
    selected_keys = set([])
    for path in final_valid_paths[path_name]:
        grad_path = [node_obj['title'] for node_obj in path]
        selected_paths.append(grad_path)
        selected_keys.add("_".join(grad_path))
    all_paths = [[path, len(path)] for path in all_paths
                 if "_".join(path) not in selected_keys]

    for i, path in enumerate(all_paths):
        similarities = []
        for selected_path in selected_paths:
            similarity = similarity_computer(path[0], selected_path)
            similarities.append(similarity)
        if similarities:
            similarity = 1 / max(similarities)
        else:
            similarity = 4
        all_paths[i].append(similarity)
        all_weights = [
            edge_weights[(path[0][j - 1], node)]['count']
            if j and (path[0][j - 1], node) in edge_weights else 0
            for j, node in enumerate(path[0])
        ]
        all_weights = sorted(all_weights)
        all_paths[i].append(all_weights[0] * len_frac[path[1]] * similarity)
        if len(all_weights) > 1:
            all_paths[i].append(all_weights[1] * len_frac[path[1]] *
                                similarity)
        else:
            all_paths[i].append(0)
        if len(all_weights) > 2:
            all_paths[i].append(all_weights[2] * len_frac[path[1]] *
                                similarity)
        else:
            all_paths[i].append(0)
        del all_weights
    try:
        all_paths = sorted(
            all_paths, key=lambda k: (k[3], k[4], k[5]), reverse=True)
        for best_path in all_paths:
            if best_path[2] >= 1:
                selected_paths.append(best_path[0])
                key = "_".join(best_path[0])
                final_valid_paths[path_name].append(path_obj[key])
                if len(selected_paths) == 15:
                    break
    except:
        pass


def combine_start_and_end_titles(titles_dict):
    sts = set()
    ets = set()
    for degree, end_titles in titles_dict["end_titles"].items():
        start_titles = titles_dict["start_titles"][degree]
        sts.update(start_titles[:30])
        ets.update(end_titles[:50])
    return [sts, ets]


def print_paths(depriotize_starts,
                major_title_dict,
                degrees,
                work_meta_info,
                min_conf,
                required_skills_threshold=5,
                top_k=30,
                edge_count_threshold=3):
    collection_name = "careerPathsForMajors5"
    title_skills = read_skill_master()
    title_time_dict = read_local_skill_master()
    for major, titles_dict in major_title_dict.items():
        start_time = time.time()
        final_valid_paths = {}
        final_valid_paths['name'] = major
        final_valid_paths['version'] = 4
        final_valid_paths['graduate_paths'] = []
        final_valid_paths['under_graduate_paths'] = []
        final_valid_paths['other_paths'] = []
        iterate_over_degrees = ["Graduate", "Under Graduate", "Other"]
        major_edge_count_threshold = 0.1  #edge_count_threshold
        [sts, ets] = combine_start_and_end_titles(titles_dict)
        edges = create_graph_for_majors(major, degrees, work_meta_info,
                                        min_conf, depriotize_starts)
        joblib.dump(
            edges, '/mnt/data/rohit/major_edge_count/' +
            "_".join(re.sub("\W+", " ", major).split()) + '_edge_counts.pkl')
        while major_edge_count_threshold > -1 and iterate_over_degrees:
            career_graph = create_graph(edges, sts, ets,
                                        major_edge_count_threshold)
            [result_paths, edges] = print_paths_iterator(
                major, titles_dict, title_skills, required_skills_threshold,
                career_graph, edges, title_time_dict, iterate_over_degrees)
            if len(result_paths['graduate_paths']
                   ) >= 15 and not final_valid_paths['graduate_paths']:
                final_valid_paths['graduate_paths'].extend(result_paths[
                    'graduate_paths'])
                iterate_over_degrees.remove("Graduate")
            elif result_paths['graduate_paths'] and len(final_valid_paths[
                    'graduate_paths']) < 15:
                append_new_paths(
                    result_paths,
                    edges,
                    final_valid_paths,
                    path_name='graduate_paths')
                if len(final_valid_paths['graduate_paths']) >= 15:
                    iterate_over_degrees.remove("Graduate")

            if len(result_paths['under_graduate_paths']
                   ) >= 15 and not final_valid_paths['under_graduate_paths']:
                final_valid_paths['under_graduate_paths'].extend(result_paths[
                    'under_graduate_paths'])
                iterate_over_degrees.remove("Under Graduate")
            elif result_paths['under_graduate_paths'] and len(
                    final_valid_paths['under_graduate_paths']) < 15:
                append_new_paths(
                    result_paths,
                    edges,
                    final_valid_paths,
                    path_name='under_graduate_paths')
                if len(final_valid_paths['under_graduate_paths']) >= 15:
                    iterate_over_degrees.remove("Under Graduate")

            if len(result_paths['other_paths']
                   ) >= 15 and not final_valid_paths['other_paths']:
                final_valid_paths['other_paths'].extend(result_paths[
                    'other_paths'])
                iterate_over_degrees.remove("Other")
            elif result_paths['other_paths'] and len(final_valid_paths[
                    'other_paths']) < 15:
                append_new_paths(
                    result_paths,
                    edges,
                    final_valid_paths,
                    path_name='other_paths')
                if len(final_valid_paths['other_paths']) >= 15:
                    iterate_over_degrees.remove("Other")
            major_edge_count_threshold -= 1

        db_local.insert_records(collection_name, final_valid_paths)

        print "Done Major: {} in {}s".format(major, time.time() - start_time)


def read_skill_master():
    skill_master_dict = {}
    cursor = dbutils.fetch_data(
        configurator.commons.SKILL_MASTER, 'cursor', {},
        {'lay_title': 1,
         'most_popular_soc_codes': 1,
         'skill_set': 1})
    for elem in cursor:
        skill_master_dict[elem['lay_title']] = {}
        skill_master_dict[elem['lay_title']]['soc_code'] = elem[
            'most_popular_soc_codes'][0]
        skill_master_dict[elem['lay_title']][
            'skill_set'] = [skill[0] for skill in elem['skill_set'][:30]]
    return skill_master_dict


def read_local_skill_master():
    skill_master_dict = {}
    cursor = db_zippia2.fetch_data(configurator.commons.SKILL_MASTER, 'cursor',
                                   {},
                                   {'lay_title': 1,
                                    'median_time_to_reach': 1})
    for elem in cursor:
        if "median_time_to_reach" in elem:
            skill_master_dict[elem['lay_title']] = {}
            skill_master_dict[elem['lay_title']] = elem['median_time_to_reach']
    return skill_master_dict


def path_main_function():
    depriotize_starts = set([
        "Assistant Internship", "Externship", "Volunteer", "Tutor",
        "Administrative Assistant", "Cashier", "Customer Service",
        "Customer Service Representative", "Server", "Bartender", "Waiter",
        "Waitress", "Instructor"
    ])
    work_start_index = 1
    work_end_index = 15
    work_prefix = "W"
    work_meta_info = []
    min_conf = 0
    degrees = set([
        "Bachelors", "Masters", "Doctorate", "Certificate", "Associate",
        "License", "Diploma", "Other"
    ])
    for index in range(work_start_index, work_end_index + 1):
        index_str = str(index)
        work_meta_info_obj = {}
        work_meta_info_obj["title"] = "closest_lay_title_" + index_str
        work_meta_info_obj["confidence"] = "max_confidence_" + index_str
        work_meta_info_obj["match"] = "is_match_" + index_str
        work_meta_info_obj["from"] = work_prefix + index_str + "Duration From"
        work_meta_info_obj["to"] = work_prefix + index_str + "Duration To"
        work_meta_info.append(work_meta_info_obj)
    major_title_dict = read_start_titles_and_end_titles(
        top_k_start=30, top_k_end=50, depriotize_starts=depriotize_starts)
    print "major title dict created successfully"
    print_paths(depriotize_starts, major_title_dict, degrees, work_meta_info,
                min_conf)
    print "Done"


if __name__ == "__main__":
    path_main_function()
