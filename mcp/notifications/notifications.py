from pushbullet.pushbullet import PushBullet
import logging

logger = None
channel = None
pb = None

def init(config):
    global logger
    global pb
    global channel
    logger = logging.getLogger(__name__)
    logger.info("Initializing notifications (pushbullet)")
    pb = PushBullet(config['pushbullet']['token'])
    channel = config['pushbullet']['channel']

def notifyDirectors(title, message):
    logger.debug("Pushing notification to %s (title = %s): %s" % (channel, title, message))
    try:
        pb.pushNote(channel, title, message, recipient_type='channel_tag')
    except Exception as e:
        logger.error("Failed to push notification %s" % title, exc_info=True)
