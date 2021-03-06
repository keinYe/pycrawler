# -*- coding:utf-8 -*-

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

Base = declarative_base()

class DataBase(object):

    def init_url(self, url):
        self.engine = create_engine(url)
        self.db_session = scoped_session(sessionmaker(bind=self.engine))
        self.session = self.db_session
        Base.metadata.create_all(self.engine)

db = DataBase()

class CRUDMixin(object):

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        return instance.save()

    def save(self):
        """Saves the object to the database."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete the object from the database."""
        db.session.delete(self)
        db.session.commit()
        return self
