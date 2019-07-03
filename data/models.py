# -*- coding:utf-8 -*-

import datetime
from data.database import Base, CRUDMixin
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
)

class Brands(Base, CRUDMixin):
    __tablename__ = 'brands'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    url = Column(String(100))
    desc = Column(Text)

    materials = relationship('Materials', backref='brands')

class Materials(Base, CRUDMixin):
    __tablename__ = 'materials'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    # brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    number = Column(String(100), unique=True, nullable=False)
    package = Column(String(50), nullable=False)
    # price
    price = relationship('Price', backref='materials')
    brand_id = Column(Integer, ForeignKey('brands.id'))

class Price(Base, CRUDMixin):
    __tablename__ = 'price'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    price = Column(Text)
    materials_id = Column(Integer, ForeignKey('materials.id'))
