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
            self.data[params['token']] = params["data"]

    @cherrypy.expose
    def showPieChart(self, token):
        return self.data[token] if token in self.data else "No pie chart found"
