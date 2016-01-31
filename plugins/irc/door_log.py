from mcp.db import db
from mcp.db.db import DoorLog, Door, Member
from mcp.irc import plugin
from sqlalchemy import or_
import logging

def configure(config):
    pass

def setup():
    global logger
    logger = logging.getLogger(__name__)
    logger.info("Setting up 'Door Log' plugin")

def show_help(connection, target):
    connection.privmsg(target, "Usage: !doorlog <door name or member name> [door name]")

@plugin.commands('doorlog')
def door_log(connection, source, target, message):
    arguments = message.split(" ")
    if len(arguments) < 2:
        show_help(connection, target)
        return

    arg1 = arguments[1]

    arg2 = None
    if len(arguments) > 2:
        arg2 = ""
        for i in range(2, len(arguments)):
            arg2 += arguments[i] + " "
    if arg2: arg2 = arg2.strip()

    logger.debug("[Door Log] Arg1 = '%s', Arg2 = '%s'" % (arg1, arg2))

    doorLog = None
    if arg2:
        doorLog = db.session.query(DoorLog).join(Member).join(Door).filter(or_(Door.name == arg2, Door.code == arg2)).filter(or_(Member.irc_name == arg1, Member.nickname == arg1, Member.fob == arg1)).order_by(DoorLog.timestamp.desc()).first()
    else:
        doorLog = db.session.query(DoorLog).join(Member).join(Door).filter(or_(Door.name == arg1, Door.code == arg1)).order_by(DoorLog.timestamp.desc()).first()

    if doorLog:
        connection.privmsg(target, "Door '%s' was last opened at %s by %s" % (doorLog.door.name, str(doorLog.timestamp), doorLog.member.getAnnounceName()))
    else:
        connection.privmsg(target, "No log matching criteria was found")
