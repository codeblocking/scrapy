#!/user/bin/python
#-*-coding:utf-8 -*-
__author__ = 'yhx'
__data__ = '2019 04 30 19:42'
from scrapy.cmdline import execute
execute(['scrapy','crawl','weibocn','--nolog',])
