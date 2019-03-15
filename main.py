# -*- coding:utf-8 -*-

import urllib2
import re

def find_number(str):
    '''
    获取每一行中的数量范围
    '''
    res = r'<td width="40%" align="right">(.*?)</td>'
    find_str = re.findall(res, str, re.S)[0]
    # 去除单位
    res_2 = '[1-9]{1}[\\d ~\\s]*\\d'
    find_str = re.findall(res_2, find_str, re.S)[0]
    # 去除字符串中的空格
    strinfo = re.compile('[\\s]')
    return re.sub(strinfo, '', find_str)

def find_price(str):
    '''
    获取每一行中的价格信息
    '''
    res = r"<p class='goldenrod'>(.*?)</p>"
    find_str = re.findall(res, str, re.S)
    # 若无对应的价格是显示 None
    if len(find_str):
        # 去除价格中的单位
        res_2 = '[1-9]{1}[\\d\\.]*'
        find_str = re.findall(res_2, find_str[0], re.S)
        return find_str[0]
    else:
        return 'None'

url = 'https://item.szlcsc.com/8796.html'
# 读取网页内容，并解码相关内容
response = urllib2.urlopen(url)
html_text = response.read().decode('utf-8')
res_tr = r'<tr class="sample_list_tr">(.*?)</tr>'
m_tr = re.findall(res_tr, html_text, re.S)
print '%4s |   %10s |  %5s' %('序号', '数量', '单价')
print "-------------------------"
for n, value in enumerate(m_tr):
    print '%4d | %10s | %5s' %(n + 1, find_number(value), find_price(value))
    print "-------------------------"
