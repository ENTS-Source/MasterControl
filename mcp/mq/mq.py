from mcp.mq.consumer import MqConsumer
from mcp.mq.publisher import MqPublisher
from mcp.db import db
from mcp.db.db import Member, MemberSubscription
from datetime import datetime
import logging
import threading
import time
import json

logger = None
config = None
consumer = None
publisher = None

def init(incConfig, obs):
    global logger
    global config
    global consumer
    global publisher
    logger = logging.getLogger(__name__)
    config = incConfig
    obs.on("door_unlock_attempt", handle_door_unlock)
    obs.on("door_ping", handle_heartbeat)
    logger.info("Initializing AMQP connection...")
    mqUsername = config.get('amqp', "username")
    mqPassword = config.get('amqp', "password")
    mqHostname = config.get('amqp', "host") + ":" + config.get('amqp', "port")
    mqUrl = "amqp://" + mqUsername + ":" + mqPassword + "@" + mqHostname
    consumer = MqConsumer(config.get('amqp', "recv_queue"), mqUrl, handle_mq_event)
    publisher = MqPublisher(config.get('amqp', "announce_exchange"), mqUrl)

    consumerThread = threading.Thread(target=consumer.start, args=[])
    consumerThread.daemon = True
    consumerThread.start()

    publisherThread = threading.Thread(target=publisher.start, args=[])
    publisherThread.daemon = True
    publisherThread.start()

def handle_door_unlock(ampMember, door, accessPermitted, fobNumber):
    ampInfo = None
    announce = False
    name = "UNKNOWN"
    if ampMember is not None:
        ampInfo = {
            "id": ampMember.id,
            "first_name": ampMember.first_name,
            "last_name": ampMember.last_name
        }
        announce = ampMember.announce
        name = ampMember.get_announce_name()
    evt = {
        "type": "UNLOCK_ATTEMPT",
        "permitted": accessPermitted,
        "doorName": door.name,
        "doorId": door.id,
        "fobNumber": fobNumber,
        "announce": announce,
        "name": name,
        "timestamp": datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        "ampInfo": ampInfo
    }
    publisher.publish(evt)

def handle_heartbeat(device):
    evt = {
        "type": "DOOR_PING",
        "timestamp": datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
        "id": device.address,
        "active": device.is_active
    }
    publisher.publish(evt)

def handle_mq_event(body):
    logger.debug("Got message: " + body)
    body = json.loads(body)
    if (body["type"] == "MEMBER_UPDATED"):
        if(body["fob_number"] == None or body["fob_number"].strip() == '' or body["fob_number"] == 'N/A'):
            body["fob_number"] = '';
        existingMember = db.session.query(Member).filter(Member.id == body["id"]).first()
        if existingMember is None:
            existingMember = Member(
                id = body["id"],
                first_name = body["first_name"],
                last_name = body["last_name"],
                announce = body["door_access"]["announce"],
                nickname = body["nickname"],
                fob = body["fob_number"],
                last_unlock = datetime.min,
                director = body["is_director"]
            )
            db.session.add(existingMember)
        else:
            existingMember.id = body["id"]
            existingMember.first_name = body["first_name"]
            existingMember.last_name = body["last_name"]
            existingMember.announce = body["door_access"]["announce"]
            existingMember.nickname = body["nickname"]
            existingMember.fob = body["fob_number"]
            existingMember.director = body["is_director"]
        db.session.query(MemberSubscription).filter(MemberSubscription.member_id == body["id"]).delete()
        for access in body["door_access"]["access"]:
            if access["end"] == None:
                access["end"] = "2999-01-01"
            dbSubscription = MemberSubscription(
                member = existingMember,
                date_from = datetime.strptime(access["start"], "%Y-%m-%d"),
                date_to = datetime.strptime(access["end"], "%Y-%m-%d"),
                buffer_days = access["buffer_days"]
            )
            db.session.add(dbSubscription)
        logger.info("Updated member entry for fob " + body['fob_number'] + " (amp id =  " + str(body["id"]) + ")")
        db.session.expire_all()
        db.session.commit()
    else:
        logger.warning("Unrecongized message received: " + body);
