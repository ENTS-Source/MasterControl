from datetime import datetime
from mcp.devices import plugin
import logging

obs = None

def configure(incConfig, incObs):
    global obs
    obs = incObs

def setup():
    global logger
    logger = logging.getLogger(__name__)
    logger.info("Setting up 'Device Status' plugin")

@plugin.command('S')
def handle_door_status(dev, cmdLine, cmdArgs):
    logger.debug('Updating device status timestamp for device %s' % dev.address)
    dev.is_active = True
    dev.last_status = datetime.now()
    obs.trigger("door_ping", dev)
