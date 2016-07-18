#!/usr/bin/env python
# encoding: utf-8

"""
@version: ??
@author: hunter
@project: spyder22mmcc
@license: Apache Licence 
@file: global_list.py
@time: 16-7-17 下午3:09
"""
TIMEOUT = 10
Referer = ['http://22mm.xiuna.com/mm/qingliang/']
Headers = {
    'Host': '22mm.xiuna.com',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Referer': 'http://22mm.xiuna.com/mm/qingliang/',
}
index_urls = []  # 目录页
suite_urls = []  # 套图首页
img_urls = []  # 图片url，套图名称{'url','title'}

indexError = []
suiteError = []
imgError = []
