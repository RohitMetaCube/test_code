from db_utils import DBUtils
import time
import numpy
import re
import utils
from sklearn.externals import joblib
from configurator import configurator


def format_date(date_string):
    date_string = re.sub("\W+", " ", date_string.lower())
    date_string = re.sub("\d+[ ]*((year)|(yr))([s]{0,1})", " ", date_string)
    date_string = re.sub("\d+[ ]*((month)|(mt))([s]{0,1})", " ", date_string)
    date_string = re.sub(" +", " ", date_string).strip()
    return date_string


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


def is_valid_work_experience(resume, current_work_ex_meta_info, min_conf=0):
    ''' Return true if this work experience looks like a valid one, false otherwise'''
    if (current_work_ex_meta_info["title"] in resume and
            resume[current_work_ex_meta_info["title"]] and
            current_work_ex_meta_info["match"] in resume and
            resume[current_work_ex_meta_info["match"]] and
            current_work_ex_meta_info["confidence"] in resume and
            resume[current_work_ex_meta_info["confidence"]] >= min_conf):
        return True
    return False


def compute_median_career_time(db_utils,
                               work_meta_info,
                               soc_level=configurator.commons.SOC_LEVEL):
    ''' Creating an array of work ex index attributes '''
    from_index = 1
    to_index = 15
    title_durations = {}
    resume_count = 0
    ''' Fetching a cursor over all non-duplicate resumes '''
    resumes = db_utils.fetch_data("resume", "cursor", {"Duplicate": False})
    ''' Iterating over the cursor to find the transition times for each title '''
    for resume in resumes:
        resume_count += 1
        if resume_count % 10000 == 0:
            print "Processed {} resumes".format(resume_count)
        career_start_date = None
        for index in range(from_index - 1, to_index):
            ''' Check whether the given work experience is a valid one, in case it is we need to do further processing otherwise not '''
            current_work_ex_meta_info = work_meta_info[index]
            if is_valid_work_experience(resume, current_work_ex_meta_info,
                                        min_conf):
                ''' This is a valid work experience, we should add the title and the time taken by this person to reach this title '''
                current_date = extract_from_date(
                    resume[current_work_ex_meta_info['from']],
                    resume[current_work_ex_meta_info['to']])
                cy = [int(x) for x in current_date.split(',')][2]
                if cy != 100000 and cy:
                    ''' From Date is valid '''
                    ''' Check whether this is the start point in this career '''
                    if not career_start_date:
                        ''' We have found the career start date '''
                        career_start_date = current_date
                    title_tuple = (
                        resume[current_work_ex_meta_info['title']],
                        resume[current_work_ex_meta_info['soc']][:soc_level])
                    if title_tuple not in title_durations:
                        title_durations[title_tuple] = []
                    [issue_flag, duration_to_reach] = utils.date_difference(
                        career_start_date, current_date)
                    if not issue_flag:
                        title_durations[title_tuple].append(duration_to_reach)
    return title_durations


def merge_all_soc_levels(title_durations):
    title_time = {}
    for title_tuple, time_list in title_durations.items():
        title = title_tuple[0]
        if title not in title_time:
            title_time[title] = []
        title_time[title].extend(time_list)
    return title_time


def update_skill_master(db_utils, title_durations):
    for title_tuple in title_durations:
        if len(title_durations[title_tuple]) > 0:
            #             print len(title_durations[title]), title, numpy.median(title_durations[title])
            db_utils.update_median_time_to_job_to_skill_master(
                title_tuple,
                numpy.median(title_durations[title_tuple]),
                len(title_durations[title_tuple]))
        else:
            print "Something went wrong with title {} (SocCode {}) which has no durations!".format(
                title_tuple[0], title_tuple[1])


if __name__ == "__main__":
    work_start_index = 1
    work_end_index = 15
    work_prefix = "W"
    work_meta_info = []
    min_conf = 0
    for index in range(work_start_index, work_end_index + 1):
        index_str = str(index)
        work_meta_info_obj = {}
        work_meta_info_obj["title"] = "closest_lay_title_" + index_str
        work_meta_info_obj["confidence"] = "max_confidence_" + index_str
        work_meta_info_obj["match"] = "is_match_" + index_str
        work_meta_info_obj["from"] = work_prefix + index_str + "Duration From"
        work_meta_info_obj["to"] = work_prefix + index_str + "Duration To"
        work_meta_info_obj['soc'] = "soc_code_" + index_str
        work_meta_info.append(work_meta_info_obj)

    start_time = time.time()
    print "Started at {}".format(start_time)
    db_utils = DBUtils(
        db_name='zippia', host='master.mongodb.d.int.zippia.com')
    title_durations = compute_median_career_time(db_utils, work_meta_info)
    joblib.dump(title_durations,
                '/mnt/data/rohit/title_time_dict_16_jan_2017.pkl')
    title_durations = merge_all_soc_levels(title_durations)
    f = open('title_time_file.csv', 'wb')
    f.write("Title\tMedian_time_to_reach\ttotal_available_times\n")
    for title, time_list in title_durations.items():
        if time_list:
            f.write('{}\t{}\t{}\n'.format(
                title, numpy.median(time_list), len(time_list)))
        else:
            print title, "has no time data."
    f.close()
    #     try:
    #         title_durations= joblib.load("/mnt/data/rohit/title_durations.pkl")
    #     except:
    #         title_durations = compute_median_career_time(db_utils, work_meta_info)
    #         joblib.dump(title_durations, '/mnt/data/rohit/title_durations.pkl')
    #     print len(title_durations)
    #     print title_durations.items()[0]
    #     update_skill_master(db_utils, title_durations)
    end_time = time.time()
    print "Done at {} in {} seconds.".format(
        end_time, int(round((end_time - start_time), 0)))
