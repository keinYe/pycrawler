# -*- coding:utf-8 -*-

from crawler.crawler import Crawler
from data.database import db
from data.models import Materials
import logging, sys, json
import logging.config
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)
import threading



def main():
    with open('database.conf','r') as confFile:
        confStr = confFile.read()
    conf = json.JSONDecoder().decode(confStr)
    db.init_url(url=conf['mariadb_url'])

    crawler1 = Crawler(1000, url='https://www.szlcsc.com/catalog.html')
    crawler2 = Crawler(1000, url='https://www.szlcsc.com/catalog.html')
    # crawler.run(url='https://item.szlcsc.com/44085.html')
    # crawler.run(url='https://www.szlcsc.com/catalog.html')
    thread_one = threading.Thread(target=crawler1.run)
    thread_two = threading.Thread(target=crawler2.run)
    thread_one.start()
    thread_two.start()
    thread_one.join()
    thread_two.join()
    print('start')

if __name__ == '__main__':
    main()
