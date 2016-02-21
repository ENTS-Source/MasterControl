from flask import Flask
from mcp.web import routes
import logging
import threading

logger = None
webApp = None

def init(config):
    global logger
    logger = logging.getLogger(__name__)
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
    webApp.run(host=host, port=port, processes=5)
