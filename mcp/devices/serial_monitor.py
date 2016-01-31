from mcp.plugins import plugins
from datetime import datetime, timedelta
from serial import Serial
import logging
import threading
import time
import os

logger = None
thread = None
serial = None

CMD_START = 0xFE
CMD_END = 0xFF

# After 15 seconds, ask for device status
HeartbeatStatusDelta = timedelta(seconds=1)
# After 2 minutes, assume device failure
HeartbeatFailureDelta = timedelta(seconds=60)

class Host:
    address = 16
    is_active = False # assume not active by default to avoid health notifications
    last_status_request = datetime.min
    last_status = datetime.min

hosts = []
hosts.append(Host())

callables = []

def init(config):
    global thread
    global logger
    global serial
    logger = logging.getLogger(__name__)

    portName = config.get('serial', 'port')
    baudRate = config.get('serial', 'baud')

    logger.info('Initializing serial monitor (%s @ %s baud)' % (portName, baudRate))
    serial = Serial(portName, baudRate, timeout=config.getint('serial', 'timeout'))

    setup_plugins(config)

    thread = threading.Thread(target=watch_serial, args=[])
    thread.daemon = True
    thread.start()

def setup_plugins(config):
    logger.info('Loading device plugins')

    dev_plugins = plugins.get_plugins(os.path.join(os.path.dirname(__file__), '../../plugins/devices'), 'plugins.devices.')
    for plugin in dev_plugins:
        if (hasattr(plugin, 'configure')):
            plugin.configure(config)
        for func in plugin.__dict__.values():
            if (hasattr(func, 'command') and hasattr(func, '__call__')):
                callables.append(func)

def watch_serial():
    logger.info('Starting serial monitor thread')
    while True:
        for host in hosts:
            try:
                # Delay at start so each attempt begins with waiting to ensure
                # devices have a delay between attempted reads.
                time.sleep(0.1)

                # If status has not been recently received, request status
                if (datetime.now() - host.last_status > HeartbeatStatusDelta):
                    # If we've request status recently, wait before requesting against
                    if (datetime.now() - host.last_status_request > HeartbeatStatusDelta):
                        host.last_status_request = datetime.now()
                        logger.debug('Sending heartbeat to address: %s' % host.address)
                        serial.write([CMD_START, ord('S'), ord('S'), CMD_END])

                cmd = serial.readline()
                try:
                    cmdStart = cmd.index(CMD_START)

                    # First byte should be a command start: Assume no command if not
                    if (cmdStart != 0): continue

                    cmdLine = bytearray(cmd[cmdStart + 1 : cmd.index(CMD_END)]).decode('utf-8')

                    logger.debug('Read command: ' + cmdLine)

                    cmdArgs = cmdLine.split(',')

                    cmdArg = cmdArgs[0]
                    cmdProcessed = False

                    for func in callables:
                        try:
                            if (cmdArg == func.command):
                                func(serial, host, cmdLine, cmdArgs)
                                cmdProcessed = True
                        except Exception as e:
                            logger.error('Error calling plugin for command %s' % cmdLine, exc_info=True)

                    if not cmdProcessed:
                        logger.error('Invalid command (%s): unknown command type' % cmdLine)
                except ValueError as e:
                    # No command found
                    pass
                except Exception as e:
                    logger.error('Error processing command (%s)' % str(bytearray(cmd)), exc_info=True)

                # If device status has not been received by failure threshold, log and notify
                # Process this after running commands so we don't get falsely notified of failures
                # due to commands going out.
                if (datetime.now() - host.last_status > HeartbeatFailureDelta):
                    logger.error('MasterControl RFID communications down! Device: %s' % host.address)

                    if host.is_active:
                        # TODO: Notify of failure
                        host.is_active = False

                    # Prevent spamming of notifications
                    host.last_status = datetime.now() - HeartbeatStatusDelta
            except IOError as e:
                pass
            except Exception as e:
                logger.error('Error reading command', exc_info=True)
                time.sleep(5)
