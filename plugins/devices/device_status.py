from datetime import datetime
from mcp.devices import plugin
import logging

def configure(config):
    pass

def setup():
    global logger
    logger = logging.getLogger(__name__)
    logger.info("Setting up 'Device Status' plugin")

@plugin.command('S')
def handle_door_status(lib, dev, cmdLine, cmdArgs):
    logger.debug('Updating device status timestamp for device %s' % dev.address)
    dev.is_active = True
    dev.last_status = datetime.now()
