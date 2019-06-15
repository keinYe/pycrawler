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
            # try:
            #     response = request.urlopen(url=product_post_url,data=date, timeout=100)
            #     html = response.read()
            # except BaseException as e:
            #     logger.info(str(page) + ' : ' + str(self.__url_queue.qsize()))
            #     logger.error("Error: {0}".format(e))
            #     return
            data = dict(json.loads(html.decode('utf-8')))
            productRecordList = data.get('productRecordList')
            if not productRecordList:
                break
            for product in productRecordList:
                item_id = product.get('productId')
                if item_id:
                    item_url = 'https://item.szlcsc.com/' + item_id + '.html'
                    if not self.url_in_bloomfilter(item_url):
                        self.url_add_bloomfilter(item_url)
                        Crawler.url_queue.put(item_url)
            page = page + 1
        logger.info(str(page) + ' : ' + str(Crawler.url_queue.qsize()))


    def __find_url(self, current_url, html):
        if re.match(r'https://list.szlcsc.com/catalog/[0-9]+.html', current_url):
            if Crawler.url_queue.qsize() > Crawler.max_url_count:
                Crawler.url_queue.put(current_url)
            else:
                self.get_product_item_url(current_url)
            return
        for link in html.find_all(name='a', href=re.compile(r'https?://list|item.szlcsc.+')):
            url = link.get('href')
            if not self.url_in_bloomfilter(url):
                if Crawler.url_queue.qsize() < Crawler.max_url_count:
                    self.url_add_bloomfilter(url)
                    Crawler.url_queue.put(url)

    def __data_save(self, data):
        if len(data) < 2:
            logger.error('data length error : len = %d' %(len(data)))
            return
        # self.save.save(data[1], data[2])
        Crawler.lock.acquire()
        Crawler.save.save_to_database(data)
        Crawler.lock.release()

    def __get_category(self, soup):
        soup_tag = soup.find('div', class_='bread_crumbs')
        if soup_tag is None:
            logger.error(soup)
            return 'None'
        category_tag = soup_tag.find(name='a', href=re.compile(r'https?://list.szlcsc.com.+'))
        if category_tag is None:
            logger.error(category_tag)
            return 'None'
        return category_tag.string

    def __get_number(self, soup):
        number_tag = soup.find('td', align='right')
        if number_tag is None:
            logger.error(soup)
            return 'None'
        else:
            str = re.search('[1-9]{1}([\\d ~\\s]*\\d)|(\\+)',
                                next(number_tag.stripped_strings),
                                re.S)
            if str is None:
                logger.error(number_tag.stripped_strings)
                return 'None'

            strinfo = re.compile('[\\s]')
            return re.sub(strinfo, '', str.group())

    def __get_price(self, soup):
        price_tag = soup.find('p', class_='goldenrod')
        if price_tag is None:
            return 'None'
        else:
            # 提取价格中的数字，至少有一位且第一位不能是'.'
            str = re.search('[0-9]{1}[\\d\\.]*',
                                next(price_tag.stripped_strings),
                                re.S)
            if str is None:
                logger.error(price_tag.stripped_strings)
                return 'None'
            return str.group()

    def __get_name(self, soup):
        name_tag = soup.find('h1', style="display: inline;font-size: 16px;")
        if name_tag is None or name_tag.string is None:
            return "None"
        return name_tag.string

    def __get_group(self, url, soup):
        if re.match(r'https?://item.szlcsc.com/[0-9]+.html$', url) is None:
            return;
        soup = soup.find_all('tr', class_='sample_list_tr')
        price_dict = {}
        for html in soup:
            number = self.__get_number(html)
            price = self.__get_price(html)
            price_dict[number] = price
        return price_dict

    def __get_brand(self, url, soup):
        brand_dict = {}
        if re.match(r'https?://item.szlcsc.com/[0-9]+.html$', url) is None:
            return brand_dict
        soup = soup.find('div', class_='product_brand_con')
        if soup is None:
            return brand_dict
        soup = soup.find_all('div', class_='item')
        for item in soup:
            str = []
            for stri in item.stripped_strings:
                str.append(stri)
            if len(str) < 2:
                continue
            if str[0] == '品　　牌：':
                brand_dict['brand'] = str[1]
            if str[0] == '厂家型号：':
                brand_dict['model'] = str[1]
            if str[0] == '商品编号：':
                brand_dict['number'] = str[1]
            if str[0] == '封装规格：':
                brand_dict['package'] = str[1]
        # logger.info(brand_dict)
        return brand_dict

    def get_html(self, url):
        if (re.match(r'https://www.szlcsc.com/catalog.html', url) is None and
            re.match(r'https?://item.szlcsc.com/[0-9]+.html$', url) is None and
            re.match(r'https://list.szlcsc.com/catalog/[0-9]+.html', url) is None):
            return {}

        try:
            response = request.urlopen(url, timeout=10)
            html = response.read()
        except BaseException as e:
            logger.error("Error: {0}".format(e))
            return ()
        soup = BeautifulSoup(html, features='lxml')
        self.__find_url(url, soup)
        if re.match(r'https?://item.szlcsc.com/[0-9]+.html$', url) is None:
            return {}
        category = self.__get_category(soup=soup)
        name = self.__get_name(soup=soup)
        price = self.__get_group(url=url, soup=soup)
        brand = self.__get_brand(url=url, soup=soup)
        materials = {'category':category, 'name':name, 'price':price}
        materials.update(brand)
        return materials

    def run(self):
        while not Crawler.url_queue.empty():
            url = Crawler.url_queue.get()
            result = self.get_html(url)
            logger.info('%s - url : %s', threading.current_thread().name, url)
            if result:
                self.__data_save(result)
            # if result is not None and len(result) > 1:
            #     self.__data_save(result)
