#!/usr/bin/env python
# encoding: utf-8

"""
@version: 2.7
@author: hunter
@project: spyder22mmcc
@license: Apache Licence
@file: beautifulGirl4.py
@time: 16-7-17 下午12:42
"""
import os
import urllib, urlparse
import urllib2
import re
from bs4 import BeautifulSoup
import threading
from multiprocessing import Process, Pool
import datetime

"""
多进程处理分类，多线程处理分页
"""
REFERER = ['http://22mm.xiuna.com/mm/%s/' % x for x in ['qingliang', 'jingyan', 'bagua', 'suren']]  # 分类主页
CATE_NAME = [u'清凉美女', u'惊艳美女', u'美女八卦', u'素人美女']  # 分类名称
HEADERS = {
    'Host': '22mm.xiuna.com',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Referer': 'http://22mm.xiuna.com/mm/qingliang/',
}

TIMEOUT = 30
TIME_PLUS = 10
TRY_TIMES = 0

suite_count_total = 0  # 总共多少套
img_count = 0  # 下载了多少张图片
suite_count = 0  # 当前共抓取套图首页个数
suite_count_down = 0  # 当前已解析套图首页个数
index_count = 0  # 已解析目录页的数量
page_count = 0  # 总目录页数量

indexError = []
suiteError = []
imgError = []

myPool = []


def step_1(cate_index):
    """
    根据类别索引获取目录页的url,得到index_urls
    :param cate_index: 分类索引编号
    :return:
    """
    headers = HEADERS.copy()
    headers['Referer'] = REFERER[cate_index]
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
    for index_url in index_urls:
        t = threading.Thread(target=step_2, args=(index_url, headers, cate_index))
        global myPool
        myPool.append(t)
        t.start()


def step_2(index_url, headers, cate_index):
    """
    根据指定目录页的url，获取该页内所有套图的主页url，得到一些suite_url
    :param index_url: 一个目录页的url
    :param headers:
    :param cate_index:分类索引编号
    :return:
    """
    request = urllib2.Request(index_url, headers=headers)
    try:
        response = urllib2.urlopen(request, timeout=TIMEOUT)
    except Exception, e:
        if index_url not in indexError:
            indexError.append(index_url)
            print '--indexError   ', index_url
            print ('message', e.message)
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
        for suite_url in suite_urls:
            step_3(suite_url, headers, cate_index)


def step_3(suite_url, headers, cate_index):
    """
    根据指定套图主页的url,获取套图内所有图片的url，得到部分img_url
    :param suite_url: 套图主页url
    :param headers:
    :param cate_index:分类索引编号
    :return:
    """
    request = urllib2.Request(headers['Referer'] + suite_url, headers=headers)
    try:
        response = urllib2.urlopen(request, timeout=TIMEOUT)
    except Exception, e:
        if suite_url not in suiteError:
            suiteError.append(suite_url)
            print '--suite_urls   ', suite_url
            print 'suite_first', ('message', e.message), ('code', e.code if hasattr(e, 'code') else '')
    else:
        html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        try:
            count = int(soup.find('span', 'fColor').nextSibling.split('/')[-1])  # 本套共多少图片
        except Exception, e:
            print e.message, suite_url
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
                        print 'suite_end', ('message', e.message), ('code', e.code if hasattr(e, 'code') else '')
                    return
                else:
                    html = response2.read()
                    soup = BeautifulSoup(html, "html.parser")
            try:
                urls = soup.find('div', id='imgString').findNext('script').text
                title = soup.find('dd', 'rtitle').findChild('strong').text
                global CATE_NAME
                if not os.path.exists('../img/%s/%s' % (CATE_NAME[cate_index], title)):
                    os.makedirs('../img/%s/%s' % (CATE_NAME[cate_index], title))
            except Exception, e:
                suiteError.append(suite_url)
                print '--suite_urls   ', suite_url
                print 'suite_end', ('message', e.message)
            else:
                img_urls = []
                urls = urls.split(';')
                for i in range(1, len(urls) - 1):
                    img_url = {'url': re.split(r'=|"', urls[i])[-2].replace('/big/', '/pic/'), 'title': title}
                    img_urls.append(img_url)
                global suite_count_down
                suite_count_down += 1
                for img_url in img_urls:
                    step_4(img_url, cate_index)


def step_4(img_url, cate_index):
    """
    根据图片的url，下载图片
    :param img_url: 图片url
    :param cate_index:分类索引编号
    :return:
    """
    url = img_url['url']
    title = img_url['title']
    parts = urlparse.urlsplit(url)
    parts = parts._replace(path=urllib.quote(parts.path.encode('utf8')))
    url = parts.geturl()
    exists = '--'
    try:
        global CATE_NAME
        if not os.path.exists('../img/' + CATE_NAME[cate_index] + '/' + title + '/' + url.split('/')[-1]):
            urllib.urlretrieve(url, '../img/' + CATE_NAME[cate_index] + '/' + title + '/' + url.split('/')[-1])
            exists = "++"
    except Exception, e:
        if img_url not in imgError:
            imgError.append(img_url)
            print '--img_urls   ', img_url['url'], img_url['title']
            print ('message', e.message)
    else:
        global img_count
        img_count += 1
        if exists == "++":
            print exists, img_count


def step_5(headers, cate_index):
    """
    检查并重新尝试出错的url
    :param headers:
    :param cate_index:分类索引编号
    :return:
    """
    print u'检查模式'
    global TIMEOUT
    global TIME_PLUS
    global TRY_TIMES
    TIMEOUT += TIME_PLUS
    TRY_TIMES += 1

    global indexError
    print u'index错误数量', len(indexError)
    for index_url in indexError[:]:
        indexError.remove(index_url)
        step_2(index_url, headers, cate_index)

    global suiteError
    print u'suite错误数量', len(suiteError)
    for suite_url in suiteError[:]:
        suiteError.remove(suite_url)
        step_3(suite_url, headers, cate_index)

    global imgError
    print u'img错误数量', len(imgError)
    for img_url in imgError[:]:
        imgError.remove(img_url)
        step_4(img_url, cate_index)
    if TRY_TIMES > 3 and (indexError or suiteError or imgError):  # 尝试3次错误处理
        step_5(headers, cate_index)


def worker(cate_index):
    start_time = datetime.datetime.now()
    print u'开始时间', start_time
    step_1(cate_index)
    global myPool
    for t in myPool:
        t.join()
    HEADERS['Referer'] = REFERER[cate_index]
    step_5(HEADERS)
    end_time = datetime.datetime.now()
    print u'结束时间', end_time, u'耗时', end_time - start_time


if __name__ == '__main__':
    p = Pool()
    for i in range(len(CATE_NAME)):
        p.apply_async(worker, args=(i,))
    p.close()
    p.join()
