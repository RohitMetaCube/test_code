import utils
from configurator import configurator
from title_duration_computer import is_valid_work_experience, extract_from_date
from bson.objectid import ObjectId
from db_utils import DBUtils


def compute_median_career_time(db_utils,
                               work_meta_info,
                               min_conf=0,
                               soc_level=configurator.commons.SOC_LEVEL):
    ''' Creating an array of work ex index attributes '''
    from_index = 1
    to_index = 15
    title_durations = {}
    resume_count = 0
    ''' Fetching a cursor over all non-duplicate resumes '''
    resumes = db_utils.fetch_data(
        "resume", "cursor", {"_id": ObjectId("57ea7dc7f9c9cfb41786b199")})
    ''' Iterating over the cursor to find the transition times for each title '''
    for resume in resumes:

        resume_count += 1
        if resume_count % 10000 == 0:
            print "Processed {} resumes".format(resume_count)
        career_start_date = None
        for index in list(reversed(range(from_index - 1, to_index))):
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
                        print "career_start_date:", career_start_date
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
    db = DBUtils(db_name='zippia', host='master.mongodb.d.int.zippia.com')
    r = compute_median_career_time(db, work_meta_info)
    for k, v in r.items():
        print k, v
