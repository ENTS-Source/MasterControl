from configparser import ConfigParser
import time
import sys
import signal
import logging
import logging.config
import os
import errno
from mcp.db import db
from mcp.devices import serial_monitor
from mcp.irc import irc
from mcp.amp import amp

print("Starting up...")

config = ConfigParser()
config.read('config/mastercontrol.ini')

# Setup logging
try:
    os.makedirs('logs')
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise
logging.config.fileConfig('config/logging.ini')
logger = logging.getLogger(__name__)

# Setup components
db.init(config)
serial_monitor.init(config)
irc.init(config)
amp.init(config)

def signal_handler(signal, frame):
    print("^C received - shutting down server.")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

print("Entering main application loop")
while(True):
    time.sleep(100)
