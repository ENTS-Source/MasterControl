from queue import Queue
from mcp.plugins import plugins
import irc.client
import logging
import threading
import os
import time

thread = None
logger = None
queue = Queue()
callables = []
connection = None
client = None
channel = None
config = None

def init(startConfig):
    global thread
    global logger
    global channel
    global config
    logger = logging.getLogger(__name__)
    config = startConfig
    channel = config.get('irc', 'chan')

    logger.info('Initializing IRC')
    setup_plugins(config)

    thread = threading.Thread(target=run_bot, args=[config])
    thread.daemon = True
    thread.start()

    time.sleep(1) # Give some time for the thread to start

# TODO: Use publish/subscribe pattern
def announceDoor(member, door):
    if not member.announce: return
    name = member.getAnnounceName()
    msg = '%s entered the %s' % (name, door.name)
    queue.put(msg)

def setup_plugins(config):
    logger.info('Loading IRC plugins')

    dev_plugins = plugins.get_plugins(os.path.join(os.path.dirname(__file__), '../../plugins/irc'), 'plugins.irc.')
    for plugin in dev_plugins:
        if (hasattr(plugin, 'configure')):
            plugin.configure(config)
        for func in plugin.__dict__.values():
            if (hasattr(func, 'commands') and hasattr(func, '__call__')):
                callables.append(func)

def sendMessages():
    message = None
    while True:
        try:
            message = queue.get()
            logger.debug('Sending message to %s: %s' % (channel, message))
            connection.privmsg(channel, message)
        except:
            logger.error("Error sending IRC message to %s: %s" % (channel, message), exc_info=True)

def connect():
    global connection
    host = config.get('irc', 'host')
    port = config.getint('irc', 'port')
    nick = config.get('irc', 'nick')
    real_name = config.get('irc', 'real_name')
    connection = client.server().connect(host, port, nick, real_name)

    connection.add_global_handler('welcome', on_connect)

def run_bot(config):
    global client
    try:
        logger.info('Starting IRC bot')

        queue.queue.clear() # Ensure clean at startup

        client = irc.client.Reactor()
        connect()

        senderThread = threading.Thread(target=sendMessages, args=[])
        senderThread.daemon = True
        senderThread.start()

        client.process_forever()
    except:
        logger.error('Error running IRC Bot', exc_info=True)

# Event handlers
def on_connect(connection, event):
    logger.debug("Joining channel %s" % channel)
    connection.join(channel)
