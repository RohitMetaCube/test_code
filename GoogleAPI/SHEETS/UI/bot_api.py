import cherrypy
from BeautifulSoup import BeautifulSoup


class botUI(object):
    def __init__(self):
        self.data = {}

    @cherrypy.expose
    def home(self):
        return open("UI/index.html")

    @cherrypy.expose
    def mbot(self):
        return open("UI/mbot.html")

    @cherrypy.expose
    def agentDomJs(self):
        return open("UI/jscripts/agentDemo.bundle.min.js")

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def setChartData(self):
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.headers['Connection'] = "close"

        if cherrypy.request.method == "POST":
            params = cherrypy.request.json
            self.data[(str(params['project']), str(params['month']),
                       str(params['year']))] = {
                           "hours_data": params["hours_data"],
                           "day_data": params["day_data"],
                           "week_data": params["week_data"],
                           "sprint_data": params["sprint_data"]
                       }

    @cherrypy.expose
    def showUserStats(self, project, month, year):
        project = str(project)
        month = str(month)
        year = str(year)
        key = (project, month, year)
        if key in self.data and self.data[key]:
            soup = BeautifulSoup(open("templates/pie_chart.html"))
            for k, v in self.data[key].items():
                print k, v
                try:
                    m = soup.find('', {'id': k})
                    m["value"] = v
                except Exception as e:
                    soup = "Error in '{}' chart data adding: {}".format(k, e)
                    break
        else:
            soup = "Data Not Found!!!"
        return soup
