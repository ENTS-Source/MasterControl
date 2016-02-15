from mcp.devices import plugin
from mcp.db import db
from mcp.db.db import Door, DoorLog, Member, AmpMember, AmpMemberSubscription
from mcp.devices import serial_monitor
from mcp.ircbot import irc_manager as irc
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

    door = db.session.query(Door).filter(Door.code == doorArg).first()
    ampMember = db.session.query(AmpMember).filter(AmpMember.fob == fobArg).first()

    member = None
    if ampMember is not None:
        member = db.session.query(Member).filter(Member.amp_user_id == ampMember.amp_id).first()
    else:
        member = db.session.query(Member).filter(Member.fob == fobArg).first()

    if member is not None and member.amp_user_id is not None and ampMember is None:
        logger.error("Failed to find aMember Pro member for fob %s" % fobArg)
        return

    if (member is None and ampMember is None):
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
        if ampMember is not None:
            logger.debug("Fob %s is in aMember Pro (User #%s)" % (ampMember.fob, ampMember.amp_id))
            if not ampMember.isFobEnabled():
                logger.warning("Fob %s exists in aMember Pro but is not enabled. AMP User #%s. ACCESS DENIED." % (ampMember.fob, ampMember.amp_id))
                return
        else:
            logger.warning("Fob %s does not exist in aMember Pro" % fobArg)
            # TODO: Reimplement notification system (events?)
            #notifyDirectors('Unregistered fob (%s) accessed the space' % fobArg, "Member was allowed access to the building. Member: %s %s (%s)" % (member.first_name, member.last_name, member.email))

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
