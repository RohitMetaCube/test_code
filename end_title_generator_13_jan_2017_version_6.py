'''
end title generation with time threshold fall-back
'''
from db_utils import DBUtils
import utils
from configurator import configurator
from collections import OrderedDict
import re
import csv

def is_valid_work_info(resume, work_info_obj, min_conf=0):

    valid = False

    if (work_info_obj["title"] in resume and resume[work_info_obj["title"]] and 

        work_info_obj["match"] in resume and resume[work_info_obj["match"]] and

        work_info_obj["confidence"] in resume and resume[work_info_obj["confidence"]] >= min_conf and

        work_info_obj["from"] in resume and resume[work_info_obj["from"]] and

        work_info_obj["to"] in resume and resume[work_info_obj["to"]]):

        ''' Valid Work Experience '''

        valid = True

    return valid

def norm_degree(degree):
    if degree in set(["Masters", "Doctorate"]):   
        degree = "Graduate"
    elif degree in set(["Bachelors"]):
        degree = "Under Graduate"
    elif degree in set(["Certificate", "Associate", "License", "Diploma"]):
        degree = "Other"
    elif degree in set(["High School", "High School Diploma"]):
        degree = None
    return degree
    
def format_date(date_string):
    date_string= re.sub("\W+", " ", date_string.lower())
    date_string= re.sub("\d+[ ]*((year)|(yr))([s]{0,1})", " ", date_string)
    date_string= re.sub("\d+[ ]*((month)|(mt))([s]{0,1})", " ", date_string)
    date_string= re.sub(" +", " ", date_string).strip()
    return date_string
    
degree_map= {
        "Graduate": ["Masters", "Doctorate"],
        "Under Graduate": ["Bachelors"],
        "Other": ["Certificate", "Associate", "License", "Diploma"]
        }
    
def create_major_titles_map(work_meta_info, end_title_limit, start_title_limit, majors, degrees):
    major_field = "latest_ed_major"

    degree_field = "latest_ed_degree"
    
    latest_ed_from = "latest_ed_from"
    
    latest_ed_to = "latest_ed_to"
    
    resumes= dbutils.fetch_data('resume', 'cursor', {'latest_ed_major':{'$in':majors}, "latest_ed_degree":{'$in':degrees}})
    
    major_title_map= {}
    
    resume_count = 0
    
    for resume in resumes:
        degree= norm_degree(resume[degree_field])
        date_string= format_date(resume[latest_ed_from])
        d, m, y = utils.formatted_date(date_string)
        is_valid_date_flag= True
        if y==100000 or not y:
            is_valid_date_flag= False
        if not is_valid_date_flag:
            date_string= format_date(resume[latest_ed_to])
            d, m, y = utils.formatted_date(date_string)
            is_valid_date_flag= True
            if y==100000 or not y:
                is_valid_date_flag= False
                
        if resume[major_field] and degree and is_valid_date_flag:
            if resume[major_field] not in major_title_map:
                major_title_map[resume[major_field]]= {}
            if degree not in major_title_map[resume[major_field]]:
                major_title_map[resume[major_field]][degree]= {}
                major_title_map[resume[major_field]][degree]["valid_resumes"] = 0
                major_title_map[resume[major_field]][degree]["title_dict"] = {}
            major_title_map[resume[major_field]][degree]["valid_resumes"]+=1
            total_exp = 0
            for work_info_obj in work_meta_info:
                if is_valid_work_info(resume, work_info_obj):
                    date_string= format_date(resume[work_info_obj['to']])
                    wtd, wtm, wty = utils.formatted_date(date_string)
                    is_valid_date_flag= True
                    to_years= 0
                    from_years= 0
                    if wty==100000 or not wty:
                        is_valid_date_flag= False
                    else:
                        to_years+= (wtd+wtm*30+wty*12*30)
                    wfy= 0
                    if not is_valid_date_flag:
                        date_string= format_date(resume[work_info_obj['from']])
                        wfd, wfm, wfy = utils.formatted_date(date_string)
                        is_valid_date_flag= True
                        if wfy==100000 or not wfy:
                            is_valid_date_flag= False
                        else:
                            from_years+= (wfd+wfm*30+wfy*12*30)
                     
                    if wfy==100000 or wty==100000 or (is_valid_date_flag and (to_years>(d+m*30+y*12*30) or (not to_years and from_years>=(d+m*30+y*12*30)))):
                        [issue_flag, years_of_exp] = utils.date_difference(resume[work_info_obj["from"]], resume[work_info_obj["to"]])
                        if not issue_flag:
                            if resume[work_info_obj["title"]] not in major_title_map[resume[major_field]][degree]["title_dict"]:
                                major_title_map[resume[major_field]][degree]["title_dict"][resume[work_info_obj["title"]]]= [0, 0, {}]
                            if (years_of_exp + total_exp) >= end_title_limit:
                                major_title_map[resume[major_field]][degree]["title_dict"][resume[work_info_obj["title"]]][1]+=1
                            if total_exp < start_title_limit:
                                major_title_map[resume[major_field]][degree]["title_dict"][resume[work_info_obj["title"]]][0]+=1
                            exp= int(years_of_exp + total_exp)
                            exp = exp if exp < end_title_limit else end_title_limit-1
                            while exp>=start_title_limit:
                                if exp not in major_title_map[resume[major_field]][degree]["title_dict"][resume[work_info_obj["title"]]][2]:
                                    major_title_map[resume[major_field]][degree]["title_dict"][resume[work_info_obj["title"]]][2][exp]= 0
                                major_title_map[resume[major_field]][degree]["title_dict"][resume[work_info_obj["title"]]][2][exp]+=1
                                exp-=1
                            if 0 not in major_title_map[resume[major_field]][degree]["title_dict"][resume[work_info_obj["title"]]][2]:
                                major_title_map[resume[major_field]][degree]["title_dict"][resume[work_info_obj["title"]]][2][0]= 0
                            major_title_map[resume[major_field]][degree]["title_dict"][resume[work_info_obj["title"]]][2][0]+=1
                            
                            total_exp += years_of_exp
        resume_count+=1
        if resume_count % 10000 == 0:
            print "{} Resumes Processed".format(resume_count)
    print "{} Resumes Processed".format(resume_count)
    return major_title_map

def clean_title(title):
    if title[0]=="(":
        return re.sub(",\d+\)", "", title[1:])
    else:
        return title

def create_depriortization_lists():
    start_depriortization_list= set()
    end_depriortization_list= set()
    f= open('/mnt/data/rohit/Career_Map_Job_Titles_Clean_up.csv', 'rb')
    fr= csv.reader(f, delimiter=',')
    head_count= 3
    for row in fr:
        if head_count:
            head_count-=1
            continue
        if row[0]:
            end_depriortization_list.add(clean_title(row[0]))  
        if row[1]:
            end_depriortization_list.add(clean_title(row[1]))
        if row[3]:
            start_depriortization_list.add(clean_title(row[3]))
        if row[4]:
            start_depriortization_list.add(clean_title(row[4]))
        if row[5]:
            start_depriortization_list.add(clean_title(row[5]))
    for t in start_depriortization_list:
        print "start--->", t
    for t in end_depriortization_list:
        print "end--->", t
    return [start_depriortization_list, end_depriortization_list]
    
if __name__ == "__main__":
    
    [start_depriortization_list, end_depriortization_list] = create_depriortization_lists()

    dbutils = DBUtils(db_name='zippia', host='master.mongodb.d.int.zippia.com')#master.mongodb.d.int.zippia.com

    degrees =[
        "Bachelors", "Masters", "Doctorate", "Certificate", "Associate",
        "License", "Diploma", "Other"
    ]

    ''' Create Education Meta Dictionary '''
    work_start_index = 1

    work_end_index = 15

    education_prefix = "E"

    work_prefix = "W"

    work_meta_info = []
    
    for index in list(reversed(range(work_start_index, work_end_index + 1))):

        index_str = str(index)

        work_meta_info_obj = {}

        work_meta_info_obj["title"] = "closest_lay_title_" + index_str

        work_meta_info_obj["confidence"] = "max_confidence_" + index_str

        work_meta_info_obj["match"] = "is_match_" + index_str

        work_meta_info_obj["from"] = work_prefix + index_str + "Duration From"

        work_meta_info_obj["to"] = work_prefix + index_str + "Duration To"

        work_meta_info.append(work_meta_info_obj)
    
    major_list= ['Dance', 'International Business', 'Pastoral Counseling and Specialized Ministries', 
                 'Parks, Recreation and Leisure Studies', 'Food Science and Technology', 'Zoology/Animal Biology',
                 'Genetics', 'Nuclear Engineering', 'Architectural Sciences and Technology', 
                 'Biomathematics, Bioinformatics, and Computational Biology', 'Agriculture', 'Petroleum Engineering']

    major_titles_map = create_major_titles_map(work_meta_info, end_title_limit= 9.0, start_title_limit= 1.0, majors=major_list, degrees=degrees)
    
    print "length total majors {}".format(len(major_titles_map))
    
    end_text_with_degree_file = open("End_Titles_individual_time.csv", "w")
    
    start_text_with_degree_file = open("Start_Titles_individual_time.csv", "w")

    major_titles_map_without_degree= {}

    for major, degree_obj in major_titles_map.items():
        
        for degree, title_object in degree_obj.items():
    
            valid_resumes= title_object["valid_resumes"]

            common_string = major + "\t" + degree + "\t" + str(valid_resumes)
                
            start_title_string= ""
            
            end_title_string= ""
            
            intermediate_titles= {}
            valid_threshold= 50
            valid_count1= 0
            valid_count2= 0
            valid_titles1= {}
            valid_titles2= {}
            for title, time_interval_object in sorted(title_object["title_dict"].items(), key=lambda k: k[1][1], reverse=True):
                if time_interval_object[1] >= 5 and time_interval_object[1] >= time_interval_object[0]:
                    valid_count1+=1
                    valid_titles1[title]= time_interval_object[1]
                for interval, exp in  sorted(time_interval_object[2].items(), key=lambda k: k[0], reverse=True):
                    if interval not in intermediate_titles:
                        intermediate_titles[interval]= {}
                    if title not in intermediate_titles[interval]:
                        intermediate_titles[interval][title]= 0
                    intermediate_titles[interval][title]+=time_interval_object[2][interval]
                
            if valid_count1 < valid_threshold:              
                for interval, title_dict in sorted(intermediate_titles.items(), key=lambda k: k[0], reverse= True):
                    if interval >= 5:
                        valid_titles1= {}  
                        valid_count1= 0
                        for title, freq in sorted(title_dict.items(), key=lambda k: k[1], reverse=True):
                            if freq>=5 and freq>=title_object["title_dict"][title][0]:
                                valid_count1+=1
                                valid_titles1[title]= freq
                        if valid_count1 >= valid_threshold:
                            break    
        
            for title, time_interval_object in sorted(title_object["title_dict"].items(), key=lambda k: k[1][0], reverse=True):
                    if time_interval_object[0] >= 5 and time_interval_object[0] > time_interval_object[1]:
                        valid_count2+=1
                        valid_titles2[title]=time_interval_object[0]
                        
            if valid_count2 < valid_threshold:              
                for interval, title_dict in sorted(intermediate_titles.items(), key=lambda k: k[0])[1:]:
                    if interval<3:
                        valid_titles2= {}  
                        valid_count2= 0
                        for title, freq in sorted(intermediate_titles[0].items(), key=lambda k: k[1], reverse=True):
                            if title in title_dict:
                                freq= freq- title_dict[title]
                            if freq>=5 and title not in valid_titles1 and freq>=title_object["title_dict"][title][1]:
                                valid_count2+=1
                                valid_titles2[title]= freq
                        if valid_count2 >= valid_threshold:
                            break
            
            for title, count in valid_titles1.items():
                if title in end_depriortization_list:
                    valid_titles1[title]= count/10 if count/10 > 5 else 5
            for title, count in valid_titles2.items():
                if title in start_depriortization_list:
                    valid_titles2[title]= count/3 if count/3 > 5 else 5
            
            if len(valid_titles1)<valid_threshold:
                for title, count in valid_titles2.items():
                    if title not in valid_titles1 or count>valid_titles1[title]:
                        valid_titles1[title]= count
            if len(valid_titles2)<valid_threshold:
                for title, count in valid_titles1.items():
                    if title not in valid_titles2 or count>valid_titles2[title]:
                        valid_titles2[title]= count
            
            
            for title, count in sorted(valid_titles1.items(), key=lambda k: k[1], reverse=True):
                end_title_string+= "\t({},{})".format(title,count)
                     
            for title, count in sorted(valid_titles2.items(), key=lambda k: k[1], reverse=True):
                start_title_string+= "\t({},{})".format(title,count)
                                    
            if end_title_string:
                end_text_with_degree_file.write(common_string + end_title_string +"\n")
            if start_title_string:
                start_text_with_degree_file.write(common_string + start_title_string +"\n")
        
    end_text_with_degree_file.close()
    
    start_text_with_degree_file.close()
    
    print "Done"
        