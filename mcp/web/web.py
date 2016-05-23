from flask import Flask
from mcp.web import routes
import logging
import threading

logger = None
webApp = None
config = None

def init(incConfig, incObs):
    global logger
    global config
    logger = logging.getLogger(__name__)
    config = incConfig
    routes.init(config)
    port = config.getint('web', 'port')
    host = config.get('web', 'host')
    logger.info("Initializing web server on %s:%s" % (host, port))

    thread = threading.Thread(target=start_server, args=[host, port])
    thread.daemon = True
    thread.start()

def start_server(host, port):
    global webApp
    webApp = Flask(__name__)
    webApp.register_blueprint(routes.apiModule, url_prefix='/api')
    webApp.run(host=host, port=port, processes=config.getint("web", "processes"))
