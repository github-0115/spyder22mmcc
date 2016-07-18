#!/usr/bin/env python
# encoding: utf-8

"""
@version: 2.7.12
@author: hunter
@project: spyder22mmcc
@license: Apache Licence 
@file: beautifulGirl.py
@time: 16-7-16 下午12:53
"""
import os
import urllib, urlparse
import urllib2
import re
from bs4 import BeautifulSoup
import threadpool

Referer = ['http://22mm.xiuna.com/mm/qingliang/']
Headers = {
    'Host': '22mm.xiuna.com',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Referer': 'http://22mm.xiuna.com/mm/qingliang/',
}
cateError = []
indexError = []
pageError = []
picError = []


def get_cate_count(headers):
    """
    获取类别下图片的总套数
    :param headers:
    :return: int-->套数
    """
    url = headers['Referer']
    request = urllib2.Request(url, headers=headers)
    try:
        response = urllib2.urlopen(request)
        html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        count_str = soup.find_all('div', 'ShowPage')[0].find_all('span')[0].get_text()
        count = int(re.findall(r'\d+\d', count_str)[0])
    except Exception, e:
        count = 0
        if headers not in cateError:
            cateError.append(headers)
    return count


def index(page, headers):
    """
    抓取抓取指定目录页的各个套图
    :param page:
    :param headers:
    :return:
    """
    if page == 1:
        url = headers['Referer'] + '/index.html'
    else:
        url = headers['Referer'] + '/index_' + str(page) + '.html'
    request = urllib2.Request(url, headers=headers)
    try:
        response = urllib2.urlopen(request)
    except Exception, e:
        if {'page': page, 'headers': headers} not in indexError:
            indexError.append({'page': page, 'headers': headers})
    else:
        html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        lines = soup.find_all('ul', 'pic')
        for i in range(1, len(lines)):
            pic = {'url': None, 'title': None}
            line_pics = lines[i].findChildren('img')
            for item in line_pics:
                pic['url'] = item.find_parent('a').attrs['href'].split('/')[-1]
                pic['title'] = item.get_text()
                # pic_list.append(pic)
                cur_page(headers, **pic)


def cur_page(headers, url, title):
    """
    抓取指定套图的各个文件
    :param headers:
    :param url:
    :param title:
    :return:
    """
    request = urllib2.Request(headers['Referer'] + url, headers=headers)
    print (u'%s       正在下载' % title)
    try:
        response = urllib2.urlopen(request)
        html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        count = int(soup.find('span', 'fColor').nextSibling.split('/')[-1])  # 本套共多少图片
        request = urllib2.Request(headers['Referer'] + url.split('.')[0] + '-' + str(count) + '.html', headers=headers)
        response = urllib2.urlopen(request)
    except Exception, e:
        print (u'%s       下载失败' % title)
        if {'headers': headers, 'url': url, 'title': title} not in pageError:
            pageError.append({'headers': headers, 'url': url, 'title': title})
    else:
        html = response.read()
        get_img_in_cur_page(html, title)


def get_img_in_cur_page(html, title):
    """
    从套图展示页面抓取图片
    :param html:
    :return:
    """
    soup = BeautifulSoup(html, "html.parser")
    try:
        urls = soup.find('div', id='imgString').findNext('script').text
    except Exception, e:
        print e.message
    else:
        urls = urls.split(';')
        for i in range(1, len(urls) - 1):
            save_img(re.split(r'=|"', urls[i])[-2].replace('/big/', '/pic/'), title)
        print (u'%s      ^_^下载完成' % title)


def save_img(url, title):
    if not os.path.exists('../img/%s' % title):
        os.makedirs('../img/%s' % title)
    try:
        parts = urlparse.urlsplit(url)
        parts = parts._replace(path=urllib.quote(parts.path.encode('utf8')))
        url = parts.geturl()
        urllib.urlretrieve(url, '../img/' + title + '/' + url.split('/')[-1])
    except Exception, e:
        print (u'%s       图片未加载' % title)
        print e.message


def download(cate):
    Headers['Referer'] = cate
    headers = Headers.copy()
    total_count = get_cate_count(headers)
    page_count = total_count / 35
    if total_count % 35 > 0:
        page_count += 1
    func_var = [(None, {'page': x, 'headers': headers}) for x in range(1, page_count + 1)]
    pool = threadpool.ThreadPool(25)
    requests = threadpool.makeRequests(index, func_var)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    deal_error()


def deal_error():
    while cateError:
        for item in cateError[:]:
            cateError.remove(item)
            download(item)
    while indexError:
        for item in indexError[:]:
            indexError.remove(item)
            index(**item)
    while pageError:
        for item in pageError[:]:
            pageError.remove(item)
            cur_page(**item)
    while picError:
        for item in picError[:]:
            picError.remove(item)
            save_img(**item)


if __name__ == '__main__':
    for s in Referer:
        download(s)
