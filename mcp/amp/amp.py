from ents import AmpApi
from mcp.db import db
from mcp.db.db import Member, MemberSubscription
from datetime import datetime
import threading
import time
import logging

logger = None
ampApi = None
thread = None
fetching = False

def init(config):
    global logger
    global ampApi
    global thread
    logger = logging.getLogger(__name__)
    url = config.get('amp', 'url')
    ampApi = AmpApi(config.get('amp', 'api_key'), url)
    logger.info("Initializing aMember Pro integration with API URL %s" % url)
    thread = threading.Thread(target=run_members_fetch, args=[])
    thread.daemon = True
    thread.start()

def run_members_fetch():
    while True:
        do_fetch_members()
        time.sleep(120)

def do_fetch_members():
    global fetching
    if (fetching):
        logger.warning("Skipping AMP fetch: Fetch in progress")
        return
    fetching = True
    logger.info('Fetching latest member information from aMember Pro')
    members = ampApi.members().all()
    for member in members:
        if member.fobNumber.strip() == '' or member.fobNumber == 'N/A':
            member.fobNumber = ''
        # First try to find the member in the database
        existingMember = db.session.query(Member).filter(Member.id == member.userId).first()
        if existingMember is None:
            logger.debug("Creating member record for AMP user #%s" % member.userId)
            existingMember = Member(
                id = member.userId,
                first_name = member.firstName,
                last_name = member.lastName,
                announce = member.mcpAnnounce,
                nickname = member.mcpNickname,
                fob = member.fobNumber,
                last_unlock = datetime.min,
                director = member.isDirector
            )
            db.session.add(existingMember)
        else:
            existingMember.first_name = member.firstName
            existingMember.last_name = member.lastName
            existingMember.announce = member.mcpAnnounce
            existingMember.nickname = member.mcpNickname
            existingMember.fob = member.fobNumber
            existingMember.director = member.isDirector
            #db.session.update(existingMember)
        db.session.query(MemberSubscription).filter(MemberSubscription.member_id == member.userId).delete()
        for access in member.access:
            dbSubscription = MemberSubscription(
                member=existingMember,
                date_from = time.strptime(access.start, "%Y-%m-%d"),
                date_to = time.strptime(access.end, "%Y-%m-%d")
            )
            db.session.add(dbSubscription)
    logger.info("Finished processing aMember Pro user database")
    db.session.expire_all()
    db.session.commit()
    fetching = False
