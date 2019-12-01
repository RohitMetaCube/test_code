#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
from bs4 import BeautifulSoup
from selenium import webdriver
import re


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
        
    def extract_profile_pic(self, soup):
        try:
            pic = soup.find('img', { "class" : "pv-top-card-section__image" })
            pic = pic['src']
        except:
            pic = soup.find('img', { "class" : "profile-photo-edit__preview" })
            pic = pic['src']
        return pic
        
    def extract_summary(self, soup):
        summary=soup.find('div', { "class" : "pv-top-card-section__summary mt4 ph2 ember-view" })
        summary = summary.getText()
        summary = re.sub("See more(\s+)See more of(.*)", '', summary.encode('utf-8')).strip()
        return summary
        
    def html_fetcher(self, profile_link):
        retry_count = 5
        user_details = {}
        user_details['url'] = profile_link
        while retry_count:
            self.driver.get(profile_link)
            html=self.driver.page_source
            soup=BeautifulSoup(html) #specify parser or it will auto-select for you
            if soup.find('div', { "class" : "pv-top-card-section__summary mt4 ph2 ember-view" }):
                user_details['summary'] = self.extract_summary(soup)
                user_details['profile_pic'] = self.extract_profile_pic(soup)
                break
            retry_count-=1
            time.sleep(20)
        print user_details

if __name__ == "__main__":
    lc = LinkdeinClient()
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
                lc.html_fetcher(profile_link)
        status = raw_input("Want to retry:(Y/n)")
        if status.lower().startswith("y"):
            continue
        break
        