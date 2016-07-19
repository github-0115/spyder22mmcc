# spyder22mmcc
第一个爬虫，爬22mm.cc上的各种美女图片
使用urllib,urllib2,beautifulsoup,threading, multiprocessing
思路：
  分析网站：
      一共四个分类，清凉，惊艳……
      每个分类分若干页，各页的url有http://22mm.xiuna.com/mm/qingliang/index_N.html的规律，根据页数改变N的数值，可得到各目录页
      目录也的每一项包含套图页的首页url
      套图页的末页html页面中有一段js代码包含了此套图所有图片的url【这节省了大量http请求时间】
  操作：
      进入分类首页，抓取总套图数量，得出总目录页数量，生成目录页url，进入各个目录页抓取套图也url，进入各套图页抓取总页数，进入套图末页抓取图片url，根据图片url下载图片
