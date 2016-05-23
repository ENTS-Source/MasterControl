import logging
from matrix_client.client import MatrixClient
from matrix_client.api import MatrixRequestError
from datetime import datetime

logger = None
client = None
config = None
room = None

def init(incConfig, obs):
    global logger
    global client
    global room
    global config
    logger = logging.getLogger(__name__)
    config = incConfig

    homeserverUrl = config.get("matrix", "hs_url")
    username = config.get("matrix", "username")
    password = config.get("matrix", "password")
    roomId = config.get("matrix", "room")

    client = MatrixClient(homeserverUrl)

    try:
        client.login_with_password(username, password)
        room = client.join_room(roomId)
        client.start_listener_thread()
    except MatrixRequestError as e:
        logger.error("Failed to communicate with Matrix (homeserver = %s, username = %s, room = %s)" % (homeserverUrl, username, roomId), exc_info=True)
        return # stop trying to configure matrix

    obs.on("door_unlock", handle_door_unlock)

def handle_door_unlock(ampMember, door):
    if not ampMember.announce: return
    diffLastUnlock = (datetime.now() - (datetime.min if (ampMember.last_unlock is None) else ampMember.last_unlock)).total_seconds()
    if (diffLastUnlock > config.getint('misc', 'announce_timeout')):
        logger.debug("Announcing member to matrix room")
        name = ampMember.get_announce_name()
        room.send_notice('%s entered the %s' % (name, door.name))
