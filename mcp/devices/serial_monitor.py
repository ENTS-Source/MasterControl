import logging
import threading
import time
import os
import sys
from serial import Serial
from datetime import datetime, timedelta
from mcp.plugins import plugins

logger = None
thread = None
serial = None
obs = None

CMD_START = '\xFE'
CMD_END = '\xFF'

HEARTBEAT_STATUS_DELTA = timedelta(seconds=15) # How often to poll for status
HEARTBEAT_FAILURE_DELTA = timedelta(seconds=120) # When a device is considered broken

callables = []

# TODO: Configurable? (should pull from DB)
class Host:
    address = 17
    is_active = False # assume not active to avoid health checks
    last_status_request = datetime.min
    last_status = datetime.min

    def __init__(self, serial):
        self._serial = serial

    def admit_access(self, doorNum):
        self._serial.write([CMD_START, ord('A'), doorNum, ord('A')^doorNum, CMD_END])

hosts = []

def init(config, obsMain):
    global thread
    global logger
    global serial
    global obs
    logger = logging.getLogger(__name__)
    obs = obsMain

    portName = config.get('serial', 'port')
    baudRate = config.get('serial', 'baud')

    logger.info("Initializing serial monitor (%s @ %s baud)" % (portName, baudRate))
    serial = Serial(portName, baudRate, timeout=config.getint('serial', 'timeout'))

    # TODO: Configurable?
    hosts.append(Host(serial))
    load_commands(config, obsMain)

    thread = threading.Thread(target=watch_serial, args=[])
    thread.daemon = True
    thread.start()

def load_commands(config, obsMain):
    logger.info("Loading serial commands")

    dev_plugins = plugins.get_plugins(os.path.join(os.path.dirname(__file__), '..', '..', 'plugins', 'devices'), 'plugins.devices.')
    for plugin in dev_plugins:
        if (hasattr(plugin, 'configure')):
            plugin.configure(config, obsMain)
        for func in plugin.__dict__.values():
            if (hasattr(func, 'command') and hasattr(func, '__call__')):
                callables.append(func)

def watch_serial():
    logger.info("Starting serial monitor thread")
    while True:
        for host in hosts:
            try:
                # Delay at start so each attempt begins with waiting to ensure devices
                # have a delay between attempted reads
                time.sleep(0.1)

                # If status has not been recently received, request status
                if (datetime.now() - host.last_status > HEARTBEAT_STATUS_DELTA):
                    # If we've request status recently, wait before requesting against
                    if(datetime.now() - host.last_status_request > HEARTBEAT_STATUS_DELTA):
                        host.last_status_request = datetime.now()
                        logger.debug("Sending heartbeat to address: %s" % host.address)
                        serial.write([CMD_START, ord('S'), ord('S'), CMD_END])

                cmd = serial.readline()
                try:
                    cmdStart = cmd.index(CMD_START)

                    # First byte should be a command start: Assume no command if not
                    if (cmdStart != 0): continue

                    cmdLine = bytearray(cmd[cmdStart + 1 : cmd.index(CMD_END)]).decode('utf-8')

                    logger.debug("Read command: %s" % cmdLine)

                    cmdArgs = cmdLine.split(',')

                    cmdArg = cmdArgs[0]
                    cmdProcessed = False

                    for func in callables:
                        try:
                            if (cmdArg == func.command):
                                func(host, cmdLine, cmdArgs)
                                cmdProcessed = True
                        except Exception as e:
                            logger.error("Error calling plugin for command %s" % cmdLine, exc_info=True)

                    if not cmdProcessed:
                        logger.error("Invalid command (%s): unknown command type" % cmdLine)
                except ValueError as e:
                    pass # no command found
                except Exception as e:
                    logger.error("Error processing command (%s)" % str(bytearray(cmd)), exc_info=True)


                # If device status has not been received by failure threshold, log and notify.
                # Process this after running commands so we don't assume a device is broken when it is
                # responding slowly to ping requests.
                if (datetime.now() - host.last_status > HEARTBEAT_FAILURE_DELTA):
                    logger.error("MasterControl RFID communications down! Device: %s" % host.address)
                    obs.trigger('device_down', host)
                    host.is_active = False
                    host.last_status = datetime.now() - HEARTBEAT_STATUS_DELTA # prevents notifification spam
            except IOError as e:
                pass
            except Exception as e:
                logger.error("Error reading command", exc_info=True)
                time.sleep(5)
