import cherrypy


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
    def setPieChart(self):
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.headers['Connection'] = "close"

        if cherrypy.request.method == "POST":
            params = cherrypy.request.json
            self.data[(str(params['project']), str(params['month']),
                       str(params['year']))] = params["data"]

    @cherrypy.expose
    def showPieChart(self, project, month, year):
        project = str(project)
        month = str(month)
        year = str(year)
        return self.data[(project, month, year
                          )] if project in self.data else "No pie chart found"
