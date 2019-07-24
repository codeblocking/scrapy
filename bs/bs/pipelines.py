# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import csv
import os

import pymongo,time,re
from .items import *

class TimePipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, UserItem) or isinstance(item, WeiboItem):
            now = time.strftime('%Y-%m-%d %H:%M', time.localtime())
            item['crawled_at'] = now
        return item
class WeiboPipeline(object):
    def parse_time(self, date):
        if re.match('刚刚', date):
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
        if re.match('\d+分钟前', date):
            minute = re.match('(\d+)', date).group(1)
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time() - float(minute) * 60))
        if re.match('\d+小时前', date):
            hour = re.match('(\d+)', date).group(1)
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time() - float(hour) * 60 * 60))
        if re.match('昨天.*', date):
            date = re.match('昨天(.*)', date).group(1).strip()
            date = time.strftime('%Y-%m-%d', time.localtime(time.time() - 24 * 60 * 60)) + ' ' + date
        if re.match('\d{2}-\d{2}', date):
            date = time.strftime('%Y-', time.localtime()) + date + ' 00:00'
        return date

    def process_item(self, item, spider):
        if isinstance(item, WeiboItem):
            if item.get('created_at'):
                item['created_at'] = item['created_at'].strip()
                item['created_at'] = self.parse_time(item.get('created_at'))
            if item.get('pictures'):
                item['pictures'] = [pic.get('url') for pic in item.get('pictures')]
        return item
class MongoPipeline(object):
    def __init__(self,host,db,port):
        self.host=host
        self.db=db
        self.port=port
    @classmethod
    def from_crawler(cls,crawler):
        return cls(
            host=crawler.settings.get('HOST'),
            db=crawler.settings.get('DB'),
            port=crawler.settings.getint('PORT')
        )
    def open_spider(self,spider):
        print('-----------------')
        self.client=pymongo.MongoClient(self.host,self.port)
        self.client[self.db][UserItem.collection].create_index([('id', pymongo.ASCENDING)])
        self.client[self.db][WeiboItem.collection].create_index([('id',pymongo.ASCENDING)])
    def close_spider(self,spider):
        self.client.close()
    def process_item(self,item,spider):
        if isinstance(item,UserItem)or isinstance(item,WeiboItem):
            self.client[self.db][item.collection].update({'id':item.get('id')},{'$set':item},True)
        if isinstance(item,UserRelationItem):
            self.client[self.db][item.collection].update({'id':item.get('id')},{
                '$addToSet':
                {
                    'follows': {'$each': item['follows']},
                    'fans': {'$each': item['fans']}
                }
            },True)
        return item
from openpyxl import Workbook
# class XlsxPipeline(object):
#     def __init__(self):
#         #创建excel，填写表头
#         self.wb = Workbook()
#         self.ws = self.wb.active
#         self.ws.append(['id_','id', 'text', ])  # 设置表头
#     def process_item(self, item, spider):  # 具体内容
#         if isinstance(item,WeiboItem):
#             line = [item['user'],item['id'],item['text']]  # 把数据中项整理出来
#             self.ws.append(line)  # 将数据需要保存的项以行的形式添加到xlsx中
#             self.wb.save(r'D:\pycharm\爬虫\data\%s.xlsx' % time.strftime('%Y-%m-%d', time.localtime(time.time())))
#         return item
class TextPipeline(object):
    def __init__(self):
        self.n=0
    def open_spider(self,spider):
        with open('D:\pycharm\爬虫\data\weibo.txt','w')as f:
            f.truncate()
    def process_item(self, item, spider):
        if isinstance(item, WeiboItem):
            self.n=self.n+1
            with open(r'D:\pycharm\爬虫\data\weibo.txt', 'a', encoding='utf-8')as f:
                f.write('%s'%self.n+'-->'+item['text'] + '\n')
        return item

class CsvPipeline(object):
    def __init__(self):
        # csv文件的位置,无需事先创
        self.i=0
        self.file ='D:\pycharm\爬虫\data\weibo.csv'
    def open_spider(self,spider):
        self.open_file = open(self.file, 'wt', encoding="utf-8-sig", newline='')
        self.writer = csv.writer(self.open_file)
        self.writer.writerow(['text'])
    def process_item(self, item, spider):
        if isinstance(item, WeiboItem):
            self.i=self.i+1
            print('第%s条数据获取成功....'%self.i  )
            self.writer.writerow([item['text']])
        return item
    def close_spider(self, spider):
        # 关闭爬虫时顺便将文件保存退出
        self.open_file.close()
