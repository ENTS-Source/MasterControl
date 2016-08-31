import logging
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timedelta

logger = None
engine = None
session = None

Base = declarative_base()

def init(config):
    global logger
    global engine
    global session
    logger = logging.getLogger(__name__)
    logger.info("Initializing database")
    engine = create_engine(config.get('database', 'connection'), pool_recycle=3600)
    Base.metadata.create_all(engine)
    Base.metadata.bind = engine
    session_factory = sessionmaker(bind=engine)
    session = scoped_session(session_factory)

# Declare entity models
class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    nickname = Column(String(255))
    fob = Column('fob_number', String(255))
    last_unlock = Column(DateTime)
    announce = Column(Boolean)
    director = Column(Boolean)
    subscriptions = relationship("MemberSubscription", back_populates="member")

    def get_announce_name(self):
        if (self.nickname is not None and self.nickname.strip() != ''):
            return self.nickname
        return self.first_name

    def has_access(self):
        if (self.director === True):
            return True
        for subscription in self.subscriptions:
            if (subscription.is_today_in_range()):
                return True
        return False

class Door(Base):
    __tablename__ = "door_cache"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

class AccessLog(Base):
    __tablename__ = "access_log"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    member_id = Column(Integer, ForeignKey('members.id'))
    member = relationship(Member)
    door_id = Column(Integer, ForeignKey('door_cache.id'))
    door = relationship(Door)
    fob = Column('fob_number', String(255))
    access_permitted = Column(Boolean)
    uploaded = Column(Boolean)

class MemberSubscription(Base):
    __tablename__ = "member_subscriptions"
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    member = relationship(Member, back_populates="subscriptions")
    date_from = Column(DateTime)
    date_to = Column(DateTime)
    buffer_days = Column(Integer)

    def is_today_in_range(self):
        now = datetime.now()
        return (now >= self.date_from and now <= self.date_to) or self.can_be_lenient(self.buffer_days)

    def can_be_lenient(self, extra_days):
        now = datetime.now()
        date_to = self.date_to + timedelta(days=extra_days)
        return now >= self.date_from and now < date_to

class LegacyFob(Base):
    __tablename__ = "fallback_fobs"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    nickname = Column(String(255))
    email = Column(String(255))
    fob_number = Column(String(255))
