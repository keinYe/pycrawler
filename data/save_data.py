# -*- coding:utf-8 -*-

from openpyxl import (
    Workbook,
    load_workbook
)
import logging
import os
from data.models import Materials, Price
from data.database import db
import json

logger = logging.getLogger(__name__)

class SaveData:
    __file_name__ = r'finally/save_data.xlsx'

    def __init__(self, file_name = r'finally/save_data.xlsx'):
        __file_name__ = file_name
        if not os.path.isfile(__file_name__):
            wb = Workbook()
            wb.save(__file_name__)

    def save(self, name, data):
        wb = load_workbook(self.__file_name__)
        ws = wb.active
        list = []
        list.append(name.encode('utf-8'))
        for key, value in data.items():
            list.append(key.encode('utf-8'))
            list.append(value.encode('utf-8'))
        ws.append(list)
        wb.save(self.__file_name__)

    def save_to_database(self, materials):
        mater = db.session.query(Materials).filter_by(number=materials.get('number', 'None')).first()
        if mater is not None:
            logger.info(mater)
            return
        material = Materials(
            name=materials.get('name', 'None'),
            category=materials.get('category', 'None'),
            brand=materials.get('brand', 'None'),
            model=materials.get('model', 'None'),
            number=materials.get('number', 'None'),
            package=materials.get('package', 'None')
        )
        price = Price(price=json.dumps(materials.get('price', {'none':'none'})))
        material.price.append(price)
        material.save()
