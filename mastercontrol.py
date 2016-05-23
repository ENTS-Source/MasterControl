import logging
import logging.config
import os
import errno
import signal
import time
from ConfigParser import ConfigParser
from observable import Observable
from mcp.db import db
from mcp.devices import serial_monitor
from mcp.matrix import matrix
from mcp.amp import amp
from mcp.web import web

print("Starting up...")

config = ConfigParser()
config.read("config/mastercontrol.ini")

# Start logging
try:
    os.makedirs('logs')
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise
logging.config.fileConfig("config/logging.ini")
logger = logging.getLogger(__name__)

# Setup components
obs = Observable()
db.init(config)
serial_monitor.init(config, obs)
matrix.init(config, obs)
amp.init(config, obs)
web.init(config, obs)

def signal_handler(signal, frame):
    print("^C received - shutting down server")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

print("Entering main application loop")
while(True):
    time.sleep(100)
