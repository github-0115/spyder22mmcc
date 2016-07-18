#!/usr/bin/env python
# encoding: utf-8

"""
@version: 2.7
@author: hunter
@project: spyder22mmcc
@license: Apache Licence
@file: beautifulGirl3.py
@time: 16-7-17 下午12:42
"""
import os
import urllib, urlparse
import urllib2
import re
from bs4 import BeautifulSoup
import threadpool
import datetime

"""
以清凉美女为例子：
1. 开始，获取目录页的url
"""
TIMEOUT = 20
Referer = ['http://22mm.xiuna.com/mm/qingliang/']
Headers = {
    'Host': '22mm.xiuna.com',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Referer': 'http://22mm.xiuna.com/mm/qingliang/',
}

suite_count_total = 0  # 总共多少套
img_count = 0  # 下载了多少张图片
suite_count = 0  # 当前共抓取套图首页个数
suite_count_down = 0  # 当前已解析套图首页个数
index_count = 0  # 已解析目录页的数量
page_count = 0  # 总目录页数量

indexError = []
suiteError = []
imgError = []


def step_1(cate_index):
    """
    根据类别索引获取目录页的url,得到index_urls
    :param cate_index: 类别索引
    :return:
    """
    headers = Headers.copy()
    headers['Referer'] = Referer[cate_index]
    url = headers['Referer']
    request = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(request, timeout=TIMEOUT)
    html = response.read()
    soup = BeautifulSoup(html, "html.parser")
    count_str = soup.find_all('div', 'ShowPage')[0].find_all('span')[0].get_text()
    global suite_count_total
    suite_count_total = int(re.findall(r'\d+\d', count_str)[0])
    global page_count
    page_count = suite_count_total / 35
    index_urls = []
    if suite_count % 35 > 0:
        page_count += 1
    for i in range(1, page_count + 1):
        if i == 1:
            index_urls.append(url)
        else:
            index_urls.append(url + 'index_' + str(i) + '.html')
    pool = threadpool.ThreadPool(len(index_urls))
    func_var = [(None, {'index_url': index_url, 'headers': headers}) for index_url in index_urls]
    requests = threadpool.makeRequests(step_2, func_var)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    # for index_url in index_urls:
    #   step_2(index_url, headers)


def step_2(index_url, headers):
    """
    根据指定目录页的url，获取该页内所有套图的主页url，得到一些suite_url
    :param index_url: 一个目录页的url
    :param headers:
    :return:
    """
    request = urllib2.Request(index_url, headers=headers)
    try:
        response = urllib2.urlopen(request, timeout=TIMEOUT)
    except Exception, e:
        if index_url not in indexError:
            indexError.append(index_url)
            print '--indexError   ', index_url
        print e.message
    else:
        html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        lines = soup.find_all('ul', 'pic')
        suite_urls = []
        for i in range(1, len(lines)):
            line_pics = lines[i].findChildren('img')
            for item in line_pics:
                suite_url = item.find_parent('a').attrs['href'].split('/')[-1]
                suite_urls.append(suite_url)
                global suite_count
                suite_count += 1
        global index_count
        index_count += 1
        if page_count - index_count < page_count / 2:
            print u'########多线程获取图片url'
            pool_2 = threadpool.ThreadPool(len(suite_urls))
            func_var = [(None, {'suite_url': suite_url, 'headers': headers}) for suite_url in suite_urls]
            requests = threadpool.makeRequests(step_3, func_var)
            [pool_2.putRequest(req) for req in requests]
            pool_2.wait()
        else:
            print u'********单线程获取图片url'
            for suite_url in suite_urls:
                step_3(suite_url, headers)


def step_3(suite_url, headers):
    """
    根据指定套图主页的url,获取套图内所有图片的url，得到部分img_url
    :param suite_url: 套图主页url
    :param headers:
    :return:
    """
    request = urllib2.Request(headers['Referer'] + suite_url, headers=headers)
    try:
        response = urllib2.urlopen(request, timeout=TIMEOUT)
    except Exception, e:
        if suite_url not in suiteError:
            suiteError.append(suite_url)
            print '--suite_urls   ', suite_url
        print e.message, ('code', e.code) if hasattr(e, 'code') else None
    else:
        html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        try:
            count = int(soup.find('span', 'fColor').nextSibling.split('/')[-1])  # 本套共多少图片
        except Exception, e:
            print suite_url
            print e.message
        else:
            if count != 1:
                request2 = urllib2.Request(headers['Referer'] + suite_url.split('.')[0] + '-' + str(count) + '.html',
                                           headers=headers)
                try:
                    response2 = urllib2.urlopen(request2, timeout=TIMEOUT)
                except Exception, e:
                    if suite_url not in suiteError:
                        suiteError.append(suite_url)
                        print '--suite_urls   ', suite_url
                    print e.message, ('code', e.code) if hasattr(e, 'code') else None
                    return
                else:
                    html = response2.read()
                    soup = BeautifulSoup(html, "html.parser")
            try:
                urls = soup.find('div', id='imgString').findNext('script').text
                title = soup.find('dd', 'rtitle').findChild('strong').text
                if not os.path.exists('../img/%s' % title):
                    os.makedirs('../img/%s' % title)
            except Exception, e:
                print suite_url
                print e.message
            else:
                img_urls = []
                urls = urls.split(';')
                for i in range(1, len(urls) - 1):
                    img_url = {'url': re.split(r'=|"', urls[i])[-2].replace('/big/', '/pic/'), 'title': title}
                    img_urls.append(img_url)
                global suite_count_down
                suite_count_down += 1
                if suite_count - suite_count_down < 100:
                    print u'&&&&&&&&多线程获取图片'
                    pool_3 = threadpool.ThreadPool(len(img_urls))
                    func_var = [(None, {'img_url': img_url}) for img_url in img_urls]
                    requests = threadpool.makeRequests(step_4, func_var)
                    [pool_3.putRequest(req) for req in requests]
                    pool_3.wait()
                else:
                    print u'$$$$$$$$单线程获取图片'
                    for img_url in img_urls:
                        step_4(img_url)


def step_4(img_url):
    """
    根据图片的url，下载图片
    :param img_url: 图片url
    :return:
    """
    url = img_url['url']
    title = img_url['title']
    parts = urlparse.urlsplit(url)
    parts = parts._replace(path=urllib.quote(parts.path.encode('utf8')))
    url = parts.geturl()
    exists = '--'
    try:
        if not os.path.exists('../img/' + title + '/' + url.split('/')[-1]):
            urllib.urlretrieve(url, '../img/' + title + '/' + url.split('/')[-1])
            exists = "++"
    except Exception, e:
        if img_url not in imgError:
            imgError.append(img_url)
            print '--img_urls   ', img_url['url'], img_url['title']
        print e.message
    else:
        global img_count
        img_count += 1
        if exists == "++":
            print exists, img_count


def step_5(headers):
    print u'检查模式'
    global TIMEOUT
    TimeOut = 50
    # global img_count
    # img_count = 0
    print u'检查index_url'
    while indexError:
        TimeOut += 3
        for index_url in indexError[:]:
            indexError.remove(index_url)
            step_2(index_url, headers)
        print len(indexError)
    TimeOut = 50
    print u'结束index_url'
    print u'检查suite_url'
    global suiteError
    while suiteError:
        pool_2 = threadpool.ThreadPool(len(suiteError))
        func_var = [(None, {'suite_url': suite_url, 'headers': headers}) for suite_url in suiteError]
        requests = threadpool.makeRequests(step_3, func_var)
        [pool_2.putRequest(req) for req in requests]
        suiteError = []
        pool_2.wait()
        print(len(suiteError))
    print u'结束suite_url'
    print u'检查img_url'
    while len(imgError) > 6:
        for img_url in imgError[:]:
            imgError.remove(img_url)
            step_4(img_url)
        print(len(imgError))
    print u'结束img_url'


def workflow(cate_index):
    start_time = datetime.datetime.now()
    print u'开始时间', start_time
    step_1(cate_index)
    Headers['Referer'] = Referer[cate_index]
    step_5(Headers)
    end_time = datetime.datetime.now()
    print u'结束时间', end_time, u'耗时', end_time - start_time


if __name__ == '__main__':
    workflow(0)
    # step_3('09411$05551.html',Headers)