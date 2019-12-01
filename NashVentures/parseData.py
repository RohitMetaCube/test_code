from BeautifulSoup import BeautifulSoup
import requests

def parser(text):
    soup = BeautifulSoup(
            text, convertEntities=BeautifulSoup.HTML_ENTITIES)
    
    table = soup.find('table', attrs={'id':'matches'})
    print table
    
        
    header = [ele.text.strip() for ele in table.find('thead').find('tr').find_all('th')]
    print header
    
    table_body = table.find('tbody')
    data = []
    rows = table_body.find_all('tr')
    for row in rows[:10]:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append(cols)
        print cols
        
def parser2(text):
    soup = BeautifulSoup(
            text, convertEntities=BeautifulSoup.HTML_ENTITIES)
    for x in soup.findAll():
        print x.text
        print "".center(100, "*")
        
        
        
        
def downloader(personName=''):
    personName = "".join(x.title() for x in personName.split())
    url= "http://www.tennisabstract.com/cgi-bin/wplayer.cgi?p={}&f=r1".format(personName)
    #url = "http://www.minorleaguesplits.com/tennisabstract/cgi-bin/jsmatches/{}.js".format(personName)
    headers = {
                'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36"
    }
    print "Fetching :",url     
    
#     response = requests.get(url, headers = headers, stream=True)
    r = requests.get(url)
    
    return r.text
    
if __name__ == "__main__":
    personName = "Maria Sakkari"
    html = downloader(personName)
    parser2(html)
    