from mcp.devices import plugin
from mcp.db import db
from mcp.db.db import Door, AccessLog, Member, MemberSubscription, LegacyFob
from datetime import datetime
import logging

config = None
obs = None

def configure(incConfig, incObs):
    global config
    global obs
    config = incConfig
    obs = incObs

def setup():
    global logger
    logger = logging.getLogger(__name__)
    logger.info("Setting up 'Door Request' plugin")

@plugin.command('R')
def handle_door_status(dev, cmdLine, cmdArgs):
    fobArg = int(cmdArgs[2])
    doorArg = int(cmdArgs[1])

    logger.debug('Incoming request for access to door #%s from fob %s' % (doorArg, fobArg))

    door = db.session.query(Door).filter(Door.id == doorArg).first()
    ampMember = db.session.query(Member).filter(Member.fob == fobArg).first()
    member = db.session.query(LegacyFob).filter(LegacyFob.fob_number == fobArg).first()

    if (door is None):
        logger.warning("Unknown door number: %s" % doorArg)
        return

    allowAccess = False
    access_log = None
    if (ampMember is None):
        if (member is None):
            access_log = AccessLog(door = door, fob = fobArg, access_permitted = False, uploaded = False)
        else:
            logger.warning("Could not find aMember Pro Member, fob found in fallback table: %s" % fobArg)
            access_log = AccessLog(door = door, fob = fobArg, access_permitted = True, uploaded = False)
            allowAccess = True
    else:
        if (ampMember.has_access()):
            access_log = AccessLog(door = door, member = ampMember, fob = fobArg, access_permitted = True, uploaded = False)
            allowAccess = True
        else:
            access_log = AccessLog(door = door, member = ampMember, fob = fobArg, access_permitted = False, uploaded = False)

    if (allowAccess and ampMember is not None):
        obs.trigger("door_unlock", ampMember, door)
        ampMember.last_unlock = datetime.now()

    if allowAccess:
        logger.info('Permitting access at door %s to fob %s' % (door.name, fobArg))
        dev.admit_access(doorArg)
    else:
        logger.warning("Access denied for fob %s" % fobArg)

    db.session.add(access_log)
    db.session.commit()
