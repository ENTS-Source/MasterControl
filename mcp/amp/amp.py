from ents import AmpApi
from mcp.db import db
from mcp.db.db import AmpMember, AmpMemberSubscription, Member
from datetime import datetime
import threading
import time
import logging

logger = None
ampApi = None
thread = None

def init(config):
    global logger
    global ampApi
    global thread
    logger = logging.getLogger(__name__)
    url = config['amp']['url']
    ampApi = AmpApi(config['amp']['api_key'], url)
    logger.info("Initializing aMember Pro integration with API URL %s" % url)
    thread = threading.Thread(target=run_members_fetch, args=[])
    thread.daemon = True
    thread.start()

def run_members_fetch():
    while True:
        do_fetch_members()
        time.sleep(120)

def do_fetch_members():
    logger.info('Fetching latest member information from aMember Pro')
    members = ampApi.members().all()
    freshMembers = 0
    previousFobs = []
    for member in db.session.query(AmpMember).all():
        previousFobs.append(member.fob)
    ampUserIds = []
    db.session.query(AmpMemberSubscription).delete()
    db.session.query(AmpMember).delete()
    for member in members:
        ampUserIds.append(member.userId)
        if member.fobNumber.strip() == '' or member.fobNumber == 'N/A':
            member.fobNumber = None
        dbAmpMember = AmpMember(
            amp_id = member.userId,
            first_name = member.firstName,
            last_name = member.lastName,
            email = member.email,
            announce = member.mcpAnnounce,
            nickname = member.mcpNickname,
            fob = member.fobNumber,
            fob_status = member.fobStatus
        )
        db.session.add(dbAmpMember)
        existingMember = db.session.query(Member).filter(Member.amp_user_id == member.userId).first()
        if existingMember is None:
            logger.debug("Creating member record for AMP user #%s" % member.userId)
            dbMember = Member(
                first_name = member.firstName,
                last_name = member.lastName,
                email = member.email,
                announce = member.mcpAnnounce,
                nickname = member.mcpNickname,
                fob = member.fobNumber,
                amp_user_id = member.userId,
                last_unlock = datetime.min
            )
            db.session.add(dbMember)
        for access in member.access:
            dbSubscription = AmpMemberSubscription(
                member=dbAmpMember,
                date_from = time.strptime(access.start, "%Y-%m-%d"),
                date_to = time.strptime(access.end, "%Y-%m-%d")
            )
            db.session.add(dbSubscription)
        if member.fobNumber not in previousFobs:
            freshMembers += 1
            # TODO: Reimplement notification system (events?)
            #notifyDirectors('Fob %s added to cache' % member.fobNumber, 'Fob assigned to %s %s (%s)' % (member.firstName, member.lastName, member.email))
            previousFobs.append(member.fobNumber)
    cleanupQuery = db.session.query(Member).filter(Member.amp_user_id, Member.amp_user_id.notin_(ampUserIds))
    removed = cleanupQuery.count()
    cleanupQuery.delete(synchronize_session=False)
    logger.info("Members added from aMember Pro: %i" % (freshMembers - removed))
    db.session.expire_all()
    db.session.commit()
