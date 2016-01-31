from mcp.devices import plugin
from mcp.db import db
from mcp.db.db import Door, DoorLog, Member
from mcp.devices import serial_monitor
from mcp.irc import irc
from datetime import datetime
import logging

config = None

def configure(incConfig):
    global config
    config = incConfig

def setup():
    global logger
    logger = logging.getLogger(__name__)
    logger.info("Setting up 'Door Request' plugin")

@plugin.command('R')
def handle_door_status(lib, dev, cmdLine, cmdArgs):
    fobArg = int(cmdArgs[2])
    doorArg = int(cmdArgs[1])

    logger.debug('Incoming request for access to door #%s from fob %s' % (doorArg, fobArg))

    member = db.session.query(Member).filter(Member.fob == fobArg).first()
    door = db.session.query(Door).filter(Door.code == doorArg).first()

    if (member is None):
        logger.warning('Unknown fob number: %s' % fobArg)

        door_log = DoorLog(message='Fob %s not found in database: %s' % (fobArg, cmdLine))
        db.session.add(door_log)
        db.session.commit()

    if (door is None):
        logger.warning('Unknown door number: %s' % doorArg)

        door_log = DoorLog(message='Door %s not found in database: %s' % (doorArg, cmdLine))
        db.session.add(door_log)
        db.session.commit()

    if (door is not None and member is not None):
        # TODO: Check membership status
        logger.info('Permitting access to %s for member #%s (%s)' % (door.name, member.id, member.fob))

        # Admit access command
        # HACK: Assuming library for incoming device is serial_monitor
        lib.write([serial_monitor.CMD_START, ord('A'), doorArg, ord('A')^doorArg, serial_monitor.CMD_END])

        door_log = DoorLog( message='%s %s (%s) entered the %s (%s)' % (member.first_name, member.last_name, member.fob, door.name, door.code),
                            member=member,
                            door=door)
        db.session.add(door_log)

        member.last_unlock = datetime.now()
        db.session.commit()

        # TODO: Event?
        diffLastUnlock = (datetime.now() - (datetime.min if (member.last_unlock is None) else member.last_unlock)).total_seconds()
        if (diffLastUnlock > config.getint('misc', 'announce_timeout')):
            logger.debug('Announcing member presence')
            irc.announceDoor(member, door)
