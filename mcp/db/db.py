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
