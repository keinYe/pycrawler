# -*- coding:utf-8 -*-

from crawler.crawler import Crawler
from data.database import DataBase
import logging, sys, json
import logging.config
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


db = DataBase()

def main():
    with open('database.conf','r') as confFile:
        confStr = confFile.read()
    logger.info(confStr)
    conf = json.JSONDecoder().decode(confStr)
    db.init_url(url=conf['mariadb_url'])
    crawler = Crawler(1000)
    logger.info('run')
    crawler.run(url='https://www.szlcsc.com/')


if __name__ == '__main__':
    main()
