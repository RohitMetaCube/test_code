# Python program to illustrate 
# desktop news notifier
import feedparser
import notify2
import os
import time
def parseFeed():
    print "I am at top"
    f = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")
    ICON_PATH = os.getcwd() + "/icon.ico"
    notify2.init('News Notify')
    print "f", f
    print "f-items: ", f["items"]
    for newsitem in f['items']: 
        n = notify2.Notification(newsitem['title'], 
                                 newsitem['summary'], 
                                 icon=ICON_PATH 
                                 )
        n.set_urgency(notify2.URGENCY_NORMAL)
        n.show()
        n.set_timeout(15000)
        time.sleep(30)
     
if __name__ == '__main__':
    parseFeed()