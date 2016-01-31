from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import logging

logger = None
engine = None
session = None

Base = declarative_base()

def init(config):
    global logger
    global engine
    global session
    logger = logging.getLogger(__name__)
    logger.info('Initializing database')
    engine = create_engine(config.get('database', 'connection'), pool_recycle=3600)
    Base.metadata.create_all(engine)
    Base.metadata.bind = engine
    session_factory = sessionmaker(bind=engine)
    session = scoped_session(session_factory)

# Declare entity models
class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    twitter_name = Column(String(100))
    nickname = Column(String(100))
    irc_name = Column(String(100))
    email = Column(String(100))
    fob = Column('fob_field', String(32))
    last_unlock = Column(DateTime)
    announce = Column(Boolean)
    amp_user_id = Column(Integer)

    def getAnnounceName(self):
        name = None
        if (self.irc_name):
            name = self.irc_name
        elif (self.nickname):
            name = self.nickname
        else:
            name = self.first_name
        return name

class Door(Base):
    __tablename__ = "doors"
    id = Column(Integer, primary_key=True)
    code = Column(Integer)
    name = Column(String(50))

class DoorLog(Base):
    __tablename__ = "door_logs"
    id = Column(Integer, primary_key=True)
    message = Column(String(1024))
    timestamp = Column(DateTime, default=datetime.now)
    member_id = Column(Integer, ForeignKey('members.id'))
    member = relationship(Member)
    door_id = Column(Integer, ForeignKey('doors.id'))
    door = relationship(Door)

class AmpMember(Base):
    __tablename__ = "amp_members"
    id = Column(Integer, primary_key=True)
    amp_id = Column(Integer)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100))
    announce = Column(Boolean)
    nickname = Column(String(100))
    fob = Column(String(100))
    fob_status = Column(String(100))
    subscriptions = relationship("AmpMemberSubscription", back_populates="member")

    def isFobEnabled(self):
        if self.fob_status == 'enabled':
            return True
        elif self.fob_status == 'disabled':
            return False
        else:
            for subscription in self.subscriptions:
                if subscription.isTodayInRange():
                    return True
        return False

class AmpMemberSubscription(Base):
    __tablename__ = "amp_member_subscriptions"
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("amp_members.id"))
    member = relationship(AmpMember, back_populates="subscriptions")
    date_from = Column(DateTime)
    date_to = Column(DateTime)

    def isTodayInRange(self):
        now = datetime.now()
        return now >= self.date_from and now <= self.date_to
