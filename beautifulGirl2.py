#!/usr/bin/env python
# encoding: utf-8

"""
@version: ??
@author: hunter
@project: spyder22mmcc
@license: Apache Licence 
@file: beautifulGirl2.py
@time: 16-7-17 下午12:42
"""
import os
import urllib, urlparse
import urllib2
import re
from bs4 import BeautifulSoup
import threadpool
import datetime
from global_list import *

"""
以清凉美女为例子：
1. 进入目录页第一页，获取总套数suite_count
2. 根据suite_count分别抓取各个目录页index_N.html，然后抓取进入套图首页的suite_url，记录未能成功访问的index_X.html到indexError
3. 根据抓取的套图首页suite_url，进入套图首页，获取该套图片个数pic_count，根据suite_url和pic_count直接访问套图最后一页，获取该套图的所有图片的url，记录未能成功访问的套图首页suite_url到suiteError
4. 根据img_url下载图片，记录未能成功下载的图片到imgError
5. 重新处理indexError，suiteError，suiteEndError，imgError中的数据
"""
img_count = 0
suite_count = 0


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
    response = urllib2.urlopen(request, timeout=TimeOut)
    html = response.read()
    soup = BeautifulSoup(html, "html.parser")
    count_str = soup.find_all('div', 'ShowPage')[0].find_all('span')[0].get_text()
    suite_count = int(re.findall(r'\d+\d', count_str)[0])
    page_count = suite_count / 35
    if suite_count % 35 > 0:
        page_count += 1
    for i in range(1, page_count + 1):
        if i == 1:
            index_urls.append(url)
            print '+index_urls   ', url
        else:
            index_urls.append(url + 'index_' + str(i) + '.html')
            print '++index_urls   ', url + 'index_' + str(i) + '.html'


def step_2(index_url, headers):
    """
    根据指定目录页的url，获取该页内所有套图的主页url，得到一些suite_url
    :param index_url: 一个目录页的url
    :param headers:
    :return:
    """
    request = urllib2.Request(index_url, headers=headers)
    try:
        response = urllib2.urlopen(request, timeout=TimeOut)
    except Exception, e:
        if index_url not in indexError:
            indexError.append(index_url)
            print '--indexError   ', index_url
        print e.message
    else:
        html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        lines = soup.find_all('ul', 'pic')
        for i in range(1, len(lines)):
            line_pics = lines[i].findChildren('img')
            for item in line_pics:
                suite_url = item.find_parent('a').attrs['href'].split('/')[-1]
                suite_urls.append(suite_url)
                global suite_count
                suite_count += 1
                print '++', suite_count, 'suite_urls   ', suite_url


def step_3(suite_url, headers):
    """
    根据指定套图主页的url,获取套图内所有图片的url，得到部分img_url
    :param suite_url: 套图主页url
    :param headers:
    :return:
    """
    request = urllib2.Request(headers['Referer'] + suite_url, headers=headers)
    try:
        response = urllib2.urlopen(request, timeout=TimeOut)
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
                request = urllib2.Request(headers['Referer'] + suite_url.split('.')[0] + '-' + str(count) + '.html',
                                          headers=headers)
                try:
                    response = urllib2.urlopen(request, timeout=TimeOut)
                except Exception, e:
                    if suite_url not in suiteError:
                        suiteError.append(suite_url)
                        print '--suite_urls   ', suite_url
                    print e.message
                    return
                else:
                    html = response.read()
                    soup = BeautifulSoup(html, "html.parser")
            try:
                urls = soup.find('div', id='imgString').findNext('script').text
                title = soup.find('dd', 'rtitle').findChild('strong').text
            except Exception, e:
                print suite_url
                print e.message
            else:
                suite_urls.remove(suite_url)
                urls = urls.split(';')
                for i in range(1, len(urls) - 1):
                    img_url = {'url': re.split(r'=|"', urls[i])[-2].replace('/big/', '/pic/'), 'title': title}
                    img_urls.append(img_url)
                    global img_count
                    img_count += 1
                    print '++', img_count, 'img_urls'


def step_4(img_url):
    """
    根据图片的url，下载图片
    :param img_url: 图片url
    :return:
    """
    url = img_url['url']
    title = img_url['title']
    if not os.path.exists('../img/%s' % title):
        os.makedirs('../img/%s' % title)
    parts = urlparse.urlsplit(url)
    parts = parts._replace(path=urllib.quote(parts.path.encode('utf8')))
    url = parts.geturl()
    try:
        urllib.urlretrieve(url, '../img/' + title + '/' + url.split('/')[-1])
    except Exception, e:
        imgError.append(img_url)
        print '--img_urls   ', img_url['url'], img_url['title']
        print e.message
    else:
        img_urls.remove(img_url)


def step_5(headers):
    del index_urls[:]
    del suite_urls[:]
    del img_urls[:]
    while indexError:
        for index_url in indexError[:]:
            indexError.remove(index_url)
            step_2(index_url, headers)
    while suiteError:
        for suite_url in suiteError[:]:
            suiteError.remove(suite_url)
            step_3(suite_url, headers)
    while imgError:
        for img_url in imgError[:]:
            imgError.remove(img_url)
            step_4(img_url)


def workflow(cate_index):
    step_1(cate_index)
    headers = Headers.copy()
    headers['Referer'] = Referer[cate_index]

    pool = threadpool.ThreadPool(25)
    pool_2 = threadpool.ThreadPool(800)
    pool_3 = threadpool.ThreadPool(20)

    func_var = [(None, {'index_url': index_url, 'headers': headers}) for index_url in index_urls]
    requests = threadpool.makeRequests(step_2, func_var)
    [pool.putRequest(req) for req in requests]
    step_2_start = datetime.datetime.now()
    print '开始抓取suite_urls', step_2_start
    pool.wait()
    print '抓取suite_urls耗时', datetime.datetime.now() - step_2_start, '共抓取', len(suite_urls), '个，错误', len(indexError), '页'

    func_var_2 = [(None, {'suite_url': suite_url, 'headers': headers}) for suite_url in suite_urls]
    requests_2 = threadpool.makeRequests(step_3, func_var_2)
    [pool_2.putRequest(req) for req in requests_2]
    step_3_start = datetime.datetime.now()
    print '开始抓取img_urls', step_3_start
    pool_2.wait()
    print '抓取img_urls耗时', datetime.datetime.now() - step_3_start, '共抓取', len(img_urls), '个，错误', len(suiteError), '套'

    func_var_3 = [(None, {'img_url': img_url}) for img_url in img_urls]
    requests_3 = threadpool.makeRequests(step_4, func_var_3)
    [pool_3.putRequest(req) for req in requests_3]
    step_4_start = datetime.datetime.now()
    print '开始下载图片', step_4_start
    pool_3.wait()
    print '下载图片耗时', datetime.datetime.now() - step_4_start
    step_5(headers)


if __name__ == '__main__':
    workflow(0)
    # step_3('09411$05551.html',Headers)
