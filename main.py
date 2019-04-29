# -*- coding:utf-8 -*-

from crawler.crawler import Crawler
from data.database import db
from data.models import Materials
import logging, sys, json
import logging.config
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)



def main():
    with open('database.conf','r') as confFile:
        confStr = confFile.read()
    conf = json.JSONDecoder().decode(confStr)
    db.init_url(url=conf['mariadb_url'])

    crawler = Crawler(1000)
    # crawler.run(url='https://item.szlcsc.com/44085.html')
    crawler.run(url='https://www.szlcsc.com/')


if __name__ == '__main__':
    main()
