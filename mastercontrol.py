import logging
import logging.config
import os
import errno
import signal
import time
import sys
from ConfigParser import ConfigParser
from observable import Observable
from mcp.db import db
from mcp.devices import serial_monitor
from mcp.mq import mq

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
mq.init(config, obs)

def signal_handler(signal, frame):
    print("^C received - shutting down server")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

print("Entering main application loop")
while(True):
    time.sleep(100)
