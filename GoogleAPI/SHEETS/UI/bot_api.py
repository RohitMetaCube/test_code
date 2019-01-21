import cherrypy

class botUI(object):
    def __init__(self):
        ''

    @cherrypy.expose
    def home(self):
        return open("UI/index.html")

    @cherrypy.expose
    def mbot(self):
        return open("UI/mbot.html")

    @cherrypy.expose
    def agentDomJs(self):
        return open("UI/jscripts/agentDemo.bundle.min.js")
