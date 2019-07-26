# -*- coding:utf-8 -*-

from urllib import request
from bs4 import BeautifulSoup
from queue import Queue
import re, urllib, json
import logging
from crawler.bloomfilter import ScalableBloomFilter
from data.save_data import SaveData
import threading

logger = logging.getLogger(__name__)

REGEX_EXP_ALL = r'https?://(www|list).szlcsc.com(/(catalog|brand))+(/[0-9]*)?.html'
REGEX_EXP_BRAND_ALL = r'https://www.szlcsc.com/brand.html'
REGEX_EXP_BRAND_LIST = r'https://list.szlcsc.com/brand/[0-9]+.html'
REGEX_EXP_CATLOG_ALL = r'https://www.szlcsc.com/catalog.html'
REGEX_EXP_CATLOG_LIST = r'https://list.szlcsc.com/catalog/[0-9]+.html'

class Crawler:
    url_queue = Queue()
    bloomfilter = ScalableBloomFilter()
    save = SaveData()
    max_url_count = 1000
    lock = threading.Lock()

    def __init__(self, url_count = 1000, url = None):
        if (Crawler.max_url_count < url_count):
            Crawler.max_url_count = url_count

        Crawler.url_queue.put(url)

    def url_in_bloomfilter(self, url):
        if url in Crawler.bloomfilter:
            return True
        return False
    def url_add_bloomfilter(self, url):
        Crawler.lock.acquire()
        Crawler.bloomfilter.add(url)
        Crawler.lock.release()

    def check_url(self, regex, url):
        if regex is None or url is None:
            return False
        if re.match(regex, url) is None:
            return False
        return True

    def read_url(self, url, data):
        try:
            response = request.urlopen(url=url, data=data, timeout=100)
            html = response.read()
        except BaseException as e:
            logger.info(str(Crawler.url_queue.qsize()))
            logger.error("Error: {0}".format(e))
            return None
        else:
            return html

    def get_product_item_url(self, current_url):
        product_post_url = 'https://list.szlcsc.com/products/list'
        query = {
            'catalogNodeId': '313',
            'pageNumber': '325',
            'querySortBySign': '0',
            'showOutSockProduct': '1'
        }

        p1 = re.compile(r'[/]([0-9]*?)[.]', re.S)
        category_id = re.findall(p1, current_url)
        logger.info(category_id)
        page = 0
        query['catalogNodeId'] = category_id[0]
        query['pageNumber'] = str(page)

        while True:
            query['pageNumber'] = str(page)
            date = urllib.parse.urlencode(query).encode('utf-8')
            html = self.read_url(product_post_url, date)
            while html is None:
                html = self.read_url(product_post_url, date)

            data = dict(json.loads(html.decode('utf-8')))
            productRecordList = data.get('productRecordList')
            if not productRecordList:
                break
            for product in productRecordList:
                number = product.get('productCode')
                name = product.get('productName')
                catalog = product.get('lightCatalogName')
                model = product.get('productModel')
                brand = product.get('lightBrandName')
                package = product.get('encapsulationModel')
                price_list = product.get('productPriceList')
                price_all = []
                if price_list and type(price_list) == list and type(price_list[0]) == dict:
                    for n in price_list:
                        price = {
                            'startNumber':n.get('startPurchasedNumber'),
                            'endNumber':n.get('endPurchasedNumber'),
                            'price':n.get('thePrice')
                        }
                        price_all.append(price)
                material = {
                    'name':name,
                    'number':number,
                    'model':model,
                    'brand':brand,
                    'package':package,
                    'catalog':catalog,
                    'price':price_all
                }
                self.__data_save(material)
            page = page + 1
        logger.info(str(page) + ' : ' + str(Crawler.url_queue.qsize()))

    def __find_url(self, current_url, html):
        for link in html.find_all(name='a', href=re.compile(REGEX_EXP_BRAND_LIST)):
            url = link.get('href')
            if not self.url_in_bloomfilter(url):
                self.url_add_bloomfilter(url)
                Crawler.url_queue.put(url)

        for link in html.find_all(name='a', href=re.compile(REGEX_EXP_CATLOG_ALL)):
            url = link.get('href')
            if not self.url_in_bloomfilter(url):
                self.url_add_bloomfilter(url)
                Crawler.url_queue.put(url)

        for link in html.find_all(name='a', href=re.compile(REGEX_EXP_CATLOG_LIST)):
            url = link.get('href')
            if not self.url_in_bloomfilter(url):
                self.url_add_bloomfilter(url)
                Crawler.url_queue.put(url)

    def str_filter_right(self, string):
        r_str = re.findall('(\(\d+\))$', string)
        if r_str and type(r_str)==list:
            return string.rstrip(r_str[0]).rstrip(' ')
        return string

    def str_filter_left(self, string):
        r_str = re.findall('^(\d{1,2}. )', string)
        if r_str and type(r_str)==list:
            return string.strip(r_str[0])
        return string

    def get_catalog_page(self, soup):
        Crawler.lock.acquire()
        catalog_a = soup.find_all('div', class_='catalog_a')
        for catalog in catalog_a:
            for tag in catalog.find_all('dl'):
                catalog_dt = tag.find('dt')
                parent = self.str_filter_right(self.str_filter_left(catalog_dt.a.string))
                Crawler.save.save_catalog_to_database(parent=parent)
                for n in tag.find_all('dd'):
                    child =self.str_filter_right(n.a.string)
                    Crawler.save.save_catalog_to_database(parent=parent, child=child)
        Crawler.lock.release()

    def __data_save(self, data):
        if len(data) < 2:
            logger.error('data length error : len = %d' %(len(data)))
            return
        # self.save.save(data[1], data[2])
        Crawler.lock.acquire()
        Crawler.save.save_material_to_database(data)
        Crawler.lock.release()

    def __brand_save(self, brand):
        if len(brand) < 1:
            logger.error('data length error : len = %d' %(len(data)))
            return
        Crawler.lock.acquire()
        Crawler.save.save_brand_to_database(brand)
        Crawler.lock.release()

    def analysis_brand_page(self, soup):
        soup_tag = soup.find('div', class_='brand-info')
        brand = {}
        if soup_tag is None:
            logger.error(soup)
            return
        name_tag = soup_tag.find('h1', class_='brand-info-name')
        if name_tag and name_tag.string:
            brand['name'] = name_tag.string
        url_tag = soup_tag.find('a', class_='blue')
        if url_tag and url_tag.string:
            brand['url'] = url_tag.string
        desc_tag = soup_tag.find('div', class_='introduce_txt')
        if desc_tag and desc_tag.string:
            brand['desc'] = desc_tag.string
        if brand.get('name'):
            self.__brand_save(brand)

    def get_html(self, url):
        if self.check_url(REGEX_EXP_ALL, url) is False:
            return {}

        try:
            response = request.urlopen(url, timeout=10)
            html = response.read()
        except BaseException as e:
            logger.error("Error: {0}".format(e))
            return ()
        soup = BeautifulSoup(html, features='lxml')
        self.__find_url(url, soup)

        if self.check_url(REGEX_EXP_CATLOG_ALL, url):
            self.get_catalog_page(soup=soup)

        if self.check_url(REGEX_EXP_BRAND_LIST, url):
            self.analysis_brand_page(soup=soup)

        if self.check_url(REGEX_EXP_CATLOG_LIST, url):
            self.get_product_item_url(url)

    def run(self):
        while not Crawler.url_queue.empty():
            url = Crawler.url_queue.get()
            logger.info('%s - url : %s', threading.current_thread().name, url)
            self.get_html(url)
