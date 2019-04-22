# -*- coding:utf-8 -*-

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class DataBase(object):
    session = None

    def init_url(self, url):
        engine = create_engine(url)
        db_session = sessionmaker(bind=engine)
        session = db_session()
        Base.metadata.create_all(engine)
