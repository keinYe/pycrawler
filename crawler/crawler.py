# -*- coding:utf-8 -*-

from urllib import request
from bs4 import BeautifulSoup
from queue import Queue
import re
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

    def __find_url(self, html):
        for link in html.find_all(name='a', href=re.compile(r'https?://list|item.szlcsc.+')):
            if self.__url_queue.qsize() > self.__max_url_count:
                return
            url = link.get('href')
            if url not in self.bloomfilter:
                self.bloomfilter.add(url)
                self.__url_queue.put(url)

    def __data_save(self, data):
        if len(data) < 2:
            logger.error('data length error : len = %d' %(len(data)))
            return
        self.save.save(data[1], data[2])



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
            str = re.search('[1-9]{1}[\\d ~\\s]*\\d',
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

    def get_html(self, url):
        try:
            response = request.urlopen(url, timeout=10)
            html = response.read()
        except BaseException as e:
            logger.error(2)
            return ()
        soup = BeautifulSoup(html, features='lxml')
        self.__find_url(soup)
        if re.match(r'https?://item.szlcsc.com/[0-9]+.html$', url) is None:
            return ();
        category = self.__get_category(soup=soup)
        name = self.__get_name(soup=soup)
        price = self.__get_group(url=url, soup=soup)
        logger.info(price)
        return (category, name, price)

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
            if result is not None and len(result) > 1:
                self.__data_save(result)
