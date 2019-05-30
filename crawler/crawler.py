# -*- coding:utf-8 -*-

from urllib import request
from bs4 import BeautifulSoup
from queue import Queue
import re, urllib, json
import logging
from crawler.bloomfilter import ScalableBloomFilter
from data.save_data import SaveData

logger = logging.getLogger(__name__)


class Crawler:

    def __init__(self, max_url_count = 1000):
        self.__max_url_count = max_url_count
        self.__url_queue = Queue()
        self.save = SaveData()
        self.bloomfilter = ScalableBloomFilter()

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
            try:
                response = request.urlopen(url=product_post_url,data=date, timeout=10)
                html = response.read()
            except BaseException as e:
                logger.error(2)
                return
            data = dict(json.loads(html.decode('utf-8')))
            productRecordList = data.get('productRecordList')
            if not productRecordList:
                break
            for product in productRecordList:
                item_id = product.get('productId')
                if item_id:
                    item_url = 'https://item.szlcsc.com/' + item_id + '.html'
                    if item_url not in self.bloomfilter:
                        self.bloomfilter.add(item_url)
                        self.__url_queue.put(item_url)
            page = page + 1


    def __find_url(self, current_url, html):
        if re.match(r'https://list.szlcsc.com/catalog/[0-9]+.html', current_url):
            if self.__url_queue.qsize() > self.__max_url_count:
                self.__url_queue.put(current_url)
            else:
                self.get_product_item_url(current_url)
            return
        logger.info('test 3')
        for link in html.find_all(name='a', href=re.compile(r'https?://list|item.szlcsc.+')):
            url = link.get('href')
            if url not in self.bloomfilter:
                if self.__url_queue.qsize() < self.__max_url_count:
                    self.bloomfilter.add(url)
                    self.__url_queue.put(url)

    def __data_save(self, data):
        if len(data) < 2:
            logger.error('data length error : len = %d' %(len(data)))
            return
        # self.save.save(data[1], data[2])
        self.save.save_to_database(data)

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
            logger.error(2)
            return ()
        logger.info('test 1')
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

    def run(self, url=None):
        if url is None:
            return
        self.__url_queue.put(url)
        count = 0
        while not self.__url_queue.empty():
            count = count + 1
            url = self.__url_queue.get()
            result = self.get_html(url)
            logger.info('url : %d, %s', count, url)
            if result:
                self.__data_save(result)
            # if result is not None and len(result) > 1:
            #     self.__data_save(result)
