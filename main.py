# -*- coding:utf-8 -*-

from urllib import request
from bs4 import BeautifulSoup
import re
import os

def get_number(tag):
    number_tag = tag.find('td', align='right')
    if number_tag is None:
        return 'None'
    else:
        price = re.search('[1-9]{1}[\\d ~\\s]*\\d',
                            next(number_tag.stripped_strings),
                            re.S).group()
        strinfo = re.compile('[\\s]')
        return re.sub(strinfo, '', price)

def get_price(tag):
    price_tag = tag.find('p', class_='goldenrod')
    if price_tag is None:
        return 'None'
    else:
        price = [price for price in price_tag.stripped_strings]
        return re.search('[1-9]{1}[\\d\\.]*', price[0], re.S).group()

def find_price_group(html):
    soup = BeautifulSoup(html, features='lxml')
    return soup.find_all('tr', class_='sample_list_tr')

url = 'https://item.szlcsc.com/8796.html'
try:
    response = request.urlopen(url, timeout=5)
except BaseException as e:
    print(e)
    os._exit()

html = response.read()

price_group = find_price_group(html=html)
print ('%3s|    %5s | %3s' %('序号', '数量', '单价'))
print ("-------------------------")
serial = 0
for group in price_group:
    if group is None:
        continue
    serial = serial + 1
    print ('%4d | %10s | %5s' %(serial, get_number(group), get_price(group)))
    print ("-------------------------")
