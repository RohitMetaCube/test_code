from db_utils import DBUtils
import time
import numpy
import re
from utils import cnv
from sklearn.externals import joblib
from configurator import configurator

def is_valid_date(date_string):
    ''' Return true if the vote is valid, false otherwise '''
    d, m, y= formatted_date(date_string)
    is_valid_date_flag= True
    if y==100000 or not y:
        is_valid_date= False
    return is_valid_date_flag
    
def formatted_date(date_string):
    date1_lower = re.sub("\(.*\)", "", date_string.lower())
    d, m , y= 0, 0, 0
    d1_tokens= re.sub("[^a-z0-9]", " ", date1_lower).split()
    if len(d1_tokens)>3:
        pass
#         print [cnv(x) for x in d1_tokens], cnv(date_string)
    else:
        for i, x in enumerate(d1_tokens):
            try:
                x_i= int(x)
                if len(x)==4:
                    y= x_i
                elif (x_i > 12 and x_i<31):
                    d= x_i
                elif x_i <= 12 and not m and d:
                    m = x_i
                elif not d and m:
                    d= x_i
                elif not m and not d and i<2 and d1_tokens[i+1] > 12 and x_i <= 12 and d1_tokens[i+1] <= 31:
                    m= x_i
                elif not m and not d and x_i < 12 and i<2 and d1_tokens[i+1][0]>='a' and d1_tokens[i+1][0]>='z':
                    d= x_i
            except:
                x_i= str(x)
                if x_i.startswith('jan'):
                    m= 1
                elif x_i.startswith('feb'):
                    m= 2
                elif x_i.startswith('mar'):
                    m= 3
                elif x_i.startswith('apr'):
                    m= 4
                elif x_i.startswith('may'):
                    m= 5
                elif x_i.startswith('jun'):
                    m= 6
                elif x_i.startswith('jul'):
                    m= 7
                elif x_i.startswith('aug'):
                    m= 8
                elif x_i.startswith('sep'):
                    m= 9
                elif x_i.startswith('oct'):
                    m= 10
                elif x_i.startswith('nov'):
                    m= 11
                elif x_i.startswith('dec'):
                    m= 12
                elif x_i.startswith('present'):
                    d, m, y= 31, 12, 100000
    return d, m, y

def data_difference_support(date1):
    m= 0
    y= 0
    date1_lower = re.search("\d+[ ]+year", date1.lower())
    if date1_lower:
        y = re.sub("[^0-9]", "", date1_lower.group())
        y = float(y) if y else 0
    date1_lower = re.search("\d+[ ]+month", date1.lower())
    if date1_lower:
        m = re.sub("[^0-9]", "", date1_lower.group())
        m = float(m) if m else 0
    issue_flag= False if (y or m) else True
    years= (y + (m*30))/365.0
    if issue_flag:
        date1_lower = re.sub("\(.*\)", "", date1.lower())
        d1_tokens= re.sub("[^a-z0-9]", " ", date1_lower).split()
        try:
            if len(d1_tokens)==4 and int(d1_tokens[0])<=12 and int(d1_tokens[2])<=12 and len(d1_tokens[1])==4 and len(d1_tokens[3])==4:
                m1, y1= int(d1_tokens[0]), int(d1_tokens[1])
                m2, y2= int(d1_tokens[2]), int(d1_tokens[3])
                dist1= y1*365+m1*30
                dist2= y2*365+m2*30
                years= abs(dist2-dist1)/365.0
                issue_flag= False
        except:
            pass
    return [issue_flag, years]

def date_difference(from_date, to_date, type="months"):
    ''' Return the difference in months if the type is "months", years otherwise '''
    ''' Returns a null if there is an invalid value for any parameter from_date, or to_date'''
    [issue_flag, years]= data_difference_support(from_date)
    if issue_flag:
        [issue_flag, years]= data_difference_support(to_date)
        if issue_flag:
            d1, m1, y1= formatted_date(from_date)
            d2, m2, y2= formatted_date(to_date)
            if y1==100000 and y2!=100000:
                d1, m1, y1= d2, m2, y2
                d2, m2, y2= 31, 12, 100000
            if not y1 and d1 and m1:
                if d1<=16:
                    y1= 2000+d1
                else:
                    y1= 1900+d1
                d1= 0
            if not y2 and d2 and m2 and d2<=16:
                if d2<=16:
                    y2= 2000+d2
                else:
                    y2= 1900+d2
                d2= 0
            issue_flag= False
            years= 0
            if ((y2==100000 or y1==100000) or
                (not y1 or not y2)):
#                 print cnv(from_date), cnv(to_date), (d1, m1, y1), (d2, m2, y2)
                issue_flag=True
            else:
                if not m1 and m2:
                    m1= 12    
                dist1= y1*365+m1*30+d1
                dist2= y2*365+m2*30+d2
                years= abs(dist2-dist1)/365.0
    return [issue_flag, years]

def is_valid_work_experience(title, closest_lay_title, from_date, to_date):
    ''' Return true if this work experience looks like a valid one, false otherwise'''
    if title or closest_lay_title or from_date or to_date:
        return True
    return False

def compute_median_career_time(db_utils, soc_level=configurator.commons.SOC_LEVEL):
    ''' Creating an array of work ex index attributes '''
    from_index = 1
    to_index = 15
    closest_lay_title_array = []
    soc_code_array= []
    work_title_array = []
    duration_to_array = []
    duration_from_array = []
    work_prefix = "W"
    title_durations = {}
    resume_count = 0
    for index in range(from_index, to_index + 1):
        index_string = str(to_index + 1 - index)
        closest_lay_title_array.append("closest_lay_title_" + index_string)
        soc_code_array.append("soc_code_" + index_string)
        work_title_array.append(work_prefix + index_string + "Title")
        duration_to_array.append(work_prefix + index_string + "Duration To")
        duration_from_array.append(work_prefix + index_string + "Duration From")
        
    ''' Fetching a cursor over all non-duplicate resumes '''
    resumes = db_utils.fetch_data("resume", "cursor", {"Duplicate":False})
    ''' Iterating over the cursor to find the transition times for each title '''
    issue_count= 0
    for resume in resumes:
        resume_count += 1
        if resume_count % 10000 == 0:
            print "Processed {} resumes. have {} issues".format(resume_count, issue_count)
        career_start_date = None
        for index in range(from_index - 1, to_index):
            if closest_lay_title_array[index] not in resume:
                continue
            closest_lay_title = resume[closest_lay_title_array[index]]
            try:
                title = resume[work_title_array[index]]
                from_date = resume[duration_from_array[index]]
                to_date = resume[duration_to_array[index]]
            except:
                issue_count+=1
                continue
            ''' Check whether the given work experience is a valid one, in case it is we need to do further processing otherwise not '''
            if is_valid_work_experience(title, closest_lay_title, from_date, to_date):
                ''' This is a valid work experience, we should add the title and the time taken by this person to reach this title '''
                if is_valid_date(from_date):
                    ''' From Date is valid '''    
                    ''' Check whether this is the start point in this career '''
                    if not career_start_date:
                        ''' We have found the career start date '''
                        career_start_date = from_date
                    title_tuple= (closest_lay_title, resume[soc_code_array[index]][:soc_level])
                    if title_tuple not in title_durations:
                        title_durations[title_tuple] = []
                    [issue_flag, duration_to_reach] = date_difference(career_start_date, from_date, type="months")
                    if not issue_flag:
                        title_durations[title_tuple].append(duration_to_reach)
    return title_durations

def update_skill_master(db_utils, title_durations):
    for title_tuple in title_durations:
        if len(title_durations[title_tuple]) > 0:
#             print len(title_durations[title]), title, numpy.median(title_durations[title])
            db_utils.update_median_time_to_job_to_skill_master(title_tuple, 
                                                               numpy.median(title_durations[title_tuple]), 
                                                               len(title_durations[title_tuple]))
        else:
            print "Something went wrong with title {} (SocCode {}) which has no durations!".format(title_tuple[0], title_tuple[1])
        
if __name__ == "__main__":
    start_time = time.time()
    print "Started at {}".format(start_time)
    db_utils = DBUtils(db_name='zippia2', host='localhost')
    try:
        title_durations= joblib.load("/mnt/data/rohit/title_durations.pkl")
    except:
        title_durations = compute_median_career_time(db_utils)
        joblib.dump(title_durations, '/mnt/data/rohit/title_durations.pkl')
    print len(title_durations)
    print title_durations.items()[0]
    update_skill_master(db_utils, title_durations)
    end_time = time.time()
    print "Done at {} in {} seconds.".format(end_time, int(round((end_time - start_time), 0)))
    