#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
from BeautifulSoup import BeautifulSoup, Tag
from selenium import webdriver
import re
from collections import OrderedDict
from pymongo import MongoClient
import config

class LinkdeinClient:
    LINKDEIN_URL = 'https://www.linkedin.com/'    
    def __init__(self):
        driver_name = raw_input("Which one Web driver you have: (Chrome/Mozilla)")
        if driver_name.lower().startswith('chrome'):
            self.driver = webdriver.Chrome() #I actually used the chromedriver and did not test firefox, but it should work.
        elif driver_name.lower().startswith('mozilla') or driver_name.lower().startswith('firefox'):
            self.driver = webdriver.Firefox()
        else:
            print "Please Install any of the web drivers."
            exit()
        self.driver.get(LinkdeinClient.LINKDEIN_URL)
        self.data = OrderedDict([
            ("profile_pic", ['img', { "class" : "pv-top-card-section__image" }]),
            ("user_name", ['h1', {"class": "pv-top-card-section__name Sans-26px-black-85%"}]),
            ("user_type", ['span', {"class": "dist-value"}]),
            ("headline", ['h2', {"class": "pv-top-card-section__headline Sans-19px-black-85%"}]),
            ("location", ["h3", {"class": "pv-top-card-section__location Sans-17px-black-70% mb1 inline-block"}]),
            ("latest_company", ["h3", {"class":"pv-top-card-section__company Sans-17px-black-70% mb1 inline-block"}]),
            ("latest_school", ["h3", {"class":"pv-top-card-section__school pv-top-card-section__school--with-separator Sans-17px-black-70% mb1 inline"}]),
            ("total_connections", ["h3", {"class": "pv-top-card-section__connections pv-top-card-section__connections--with-separator Sans-17px-black-70% mb1 inline-block"}]),
            ("summary" , ['div', { "class" : "pv-top-card-section__summary mt4 ph2 ember-view" }]),
            ("experience", ["section", {"class": "pv-profile-section experience-section ember-view"}])
        ])
            
        
    def filter_experiences(self, experience_tag):
        work_exps = []
        experience_soup = BeautifulSoup(str(experience_tag), convertEntities=BeautifulSoup.HTML_ENTITIES)
        list_of_experiences = experience_soup.findAll("div", {"class": "pv-profile-section__sortable-card-item pv-position-entity ember-view"})
        for work_exp in list_of_experiences:
            new_work_ex_data = {}
            for work_ex in work_exp.findAll():
                try:
                    wx_att = dict(work_ex.attrs)
                    if "class" in wx_att:
                        if work_ex.name == 'img' and "logo-img" in wx_att['class']:
                            try:
                                new_work_ex_data['company_logo'] = wx_att['src'] if 'src' in wx_att else ''
                            except:
                                pass
                        elif work_ex.name == 'h3':
                            new_work_ex_data['job_title'] = work_ex.getText()
                        elif work_ex.name == 'span' and wx_att['class'] == "pv-entity__secondary-title":
                            new_work_ex_data['company_name'] = work_ex.getText()
                        elif work_ex.name == 'h4' and "date-range" in wx_att['class']:
                            new_work_ex_data['date_range'] = [x.getText() for x in  work_ex.contents if isinstance(x, Tag)][-1]
                        elif work_ex.name == 'h4' and "location" in wx_att['class']:
                            new_work_ex_data['location'] = [x.getText() for x in  work_ex.contents if isinstance(x, Tag)][-1]
                        elif work_ex.name == 'div' and wx_att['class'] == "pv-entity__extra-details":
                            new_work_ex_data['description'] = work_ex.getText()
                except Exception as e:
                    print e
                    continue
            work_exps.append(new_work_ex_data)
        return work_exps
    
        
    def data_cleaner(self, soup):
        clean_data= {}
        for k, v in self.data.items():
            try:
                result_tag = soup.find(v[0], v[1])
                if v[0] =='img': 
                    result_text = result_tag['src']
                else:
                    result_text = result_tag.getText() if result_tag else '' 
                    if k == "total_connections":
                        result_text = re.sub('\n+', '', re.sub("\n\d+([\+]{0,1}) connections(.*)",'', result_text)).strip()
                    elif k=="experience":
                        result_text = self.filter_experiences(result_tag) if result_tag else []
                    else:
                        result_text = re.sub("See more(\s+)See more of(.*)", '', result_text.encode('utf-8')).strip()
                        result_text = re.sub(" +", ' ', re.sub("((\n)|(\t))+", ' ', result_text)).strip()
                clean_data[k] = result_text
            except Exception as e:
                print e
                pass
        return clean_data
            
    def html_fetcher(self, profile_link):
        retry_count = config.RETRY_COUNTER
        user_details = {}
        user_details['url'] = profile_link
        while retry_count:
            self.driver.get(profile_link)
            time.sleep(config.WEB_PAGE_LOADING_TIME)
            html=self.driver.page_source
            soup=BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES) #specify parser or it will auto-select for you
            if soup.find('div', { "class" : "pv-top-card-section__summary mt4 ph2 ember-view" }):
                user_details.update(self.data_cleaner(soup))
                break
            retry_count-=1
            time.sleep(config.SLEEP_TIME_BEFORE_RETRY)
        print user_details


class MongoController:
    def __init__(self):
        client = MongoClient(config.MONGODB_HOST, config.MONGODB_PORT)
        self.db = client[config.DB_NAME]
        
    def insert_into_db(self, collection_name, records):
        self.db[collection_name].insert(records)
    


if __name__ == "__main__":
    lc = LinkdeinClient()
    moc = MongoController()
    
    profile_links= [
        "https://www.linkedin.com/in/rohit-kumar-6366a097/",
        "https://www.linkedin.com/in/neerajkumarshah",
        "https://www.linkedin.com/in/johnsmith1",
        "https://www.linkedin.com/in/rohit-kumar-46636479"
    ]
    
    while True:
        status = raw_input("Are You Readey:(Y/n)")
        if status.lower().startswith("y"):
            for profile_link in profile_links:
                user_details = lc.html_fetcher(profile_link)
                moc.insert_into_db(config.COLLECTION_NAME, user_details)
        status = raw_input("Want to retry:(Y/n)")
        if status.lower().startswith("y"):
            continue
        break
        