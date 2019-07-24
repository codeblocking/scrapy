# -*- coding: utf-8 -*-
import scrapy,json,time,re
from scrapy import Request
from ..items import *
class WeibocnSpider(scrapy.Spider):
    name = 'weibocn'
    allowed_domains = ['m.weibo.cn']
    user_url = 'https://m.weibo.cn/api/container/getIndex?uid={uid}&luicode=10000011&lfid=230413{uid}_-_WEIBO_SECOND_PROFILE_WEIBO&type=uid&value={uid}&containerid=100505{uid}'#用户的个人详情连接
    follow_url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_followers_-_{uid}&page={page}'#用户的关注列表（好友）的url
    fan_url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{uid}&page={page}'#用户的粉丝（好友)
    # weibo_url = 'https://m.weibo.cn/api/container/getIndex?uid={uid}&luicode=10000011&lfid=23041{uid}_-_WEIBO_SECOND_PROFILE_WEIBO&type=uid&value={uid}&containerid=100505{uid}'#用户的微博内容连接
    # https: // m.weibo.cn/api/container/getIndex?uid={uid}&luicode=10000011&lfid=107603{uid}&containerid=107603{uid}
    weibo_url='https://m.weibo.cn/api/container/getIndex?containerid=230413{uid}_-_WEIBO_SECOND_PROFILE_WEIBO&page_type=03&page={page}'
    start_urls = [user_url,'http://m.weibo.cn/']
    # uuid=input('请输入用户id:').strip()
    start_users = ['3217179555']
    def start_requests(self):
        for uid in self.start_users:
            yield Request(self.user_url.format(uid=uid),callback=self.parse_user)
    def parse_user(self,response):
        """解析用户信息"""
        self.logger.debug(response)
        time.sleep(1)
        result = json.loads(response.text)
        if result.get('data').get('userInfo'):
            user_info = result.get('data').get('userInfo')
            # print("用户信息：", user_info)
            user_item = UserItem()
            field_map = {
                'id': 'id', 'name': 'screen_name', 'avatar': 'profile_image_url', 'cover': 'cover_image_phone',
                'gender': 'gender', 'description': 'description', 'fans_count': 'followers_count',
                'follows_count': 'follow_count', 'weibos_count': 'statuses_count', 'verified': 'verified',
                'verified_reason': 'verified_reason', 'verified_type': 'verified_type'
            }
            for field, attr in field_map.items():
                user_item[field] = user_info.get(attr)
            yield user_item
            # 关注
            uid = user_info.get('id')
            yield Request(self.follow_url.format(uid=uid, page=1), callback=self.parse_follows,
                          meta={'page': 1, 'uid': uid})
            # 粉丝
            yield Request(self.fan_url.format(uid=uid, page=1), callback=self.parse_fans, meta={'page': 1, 'uid': uid})
            # 微博
            yield Request(self.weibo_url.format(uid=uid, page=1), callback=self.parse_weibos, meta={'page': 1, 'uid': uid})

    def parse_follows(self,response):
        result = json.loads(response.text)
        if result.get('ok') and result.get('data').get('cards') and len(result.get('data').get('cards')) and \
                result.get('data').get('cards')[-1].get('card_group'):
            # 解析用户
            follows = result.get('data').get('cards')[-1].get('card_group')
            # 对当前用户所关注的人的信息进行获取
            for follow in follows:
                if follow.get('user'):
                    uid = follow.get('user').get('id')
                    yield Request(self.user_url.format(uid=uid), callback=self.parse_user)
            uid = response.meta.get('uid')
            # 关注列表
            user_relation_item = UserRelationItem()
            follows = [{'id': follow.get('user').get('id'), 'name': follow.get('user').get('screen_name')} for follow in
                       follows]
            # 对关注用户的微博进行获取
            for i in follows:
                ui=i['id']
                yield Request(self.weibo_url.format(uid=ui, page=1), callback=self.parse_weibos,
                              meta={'page': 1, 'uid': uid})
            user_relation_item['id'] = uid
            user_relation_item['follows'] = follows
            user_relation_item['fans'] = []
            # print(user_relation_item.__dict__)
            yield user_relation_item

            # 下一页关注
            page = response.meta.get('page') + 1
            yield Request(self.follow_url.format(uid=uid, page=page), callback=self.parse_follows,
                          meta={'page': page, 'uid': uid})

    def parse_fans(self,response):
        time.sleep(1)
        result = json.loads(response.text)
        if result.get('ok') and result.get('data').get('cards') and len(result.get('data').get('cards')) and \
                result.get('data').get('cards')[-1].get('card_group'):
            # 解析用户
            fans = result.get('data').get('cards')[-1].get('card_group')
            # 获取粉丝的微博
            for fan in fans:
                if fan.get('user'):
                    uid = fan.get('user').get('id')
                    yield Request(self.weibo_url.format(uid=uid,), callback=self.parse_weibos)
            fann = []
            uid = response.meta.get('uid')

            # 粉丝列表
            user_relation_item = UserRelationItem()
            fans = [{'id': fan.get('user').get('id'), 'name': fan.get('user').get('screen_name')} for fan in fans]
            user_relation_item['id'] = uid
            if fans not in fann:
                user_relation_item['fans'] = fans

            fann.append(fans)
            user_relation_item['follows'] = []

            yield user_relation_item
            # 下一页粉丝
            page = response.meta.get('page') + 1
            yield Request(self.fan_url.format(uid=uid, page=page), callback=self.parse_fans,
                          meta={'page': page, 'uid': uid})
    def parse_weibos(self,response):
        """
               解析微博列表
               :param response: Response对象
               """
        result = json.loads(response.text)
        # print(result)
        if result.get('ok') and result.get('data').get('cards'):
            weibos = result.get('data').get('cards')
            for weibo in weibos:
                mblog = weibo.get('mblog')
                if mblog:
                    weibo_item = WeiboItem()
                    field_map = {
                        'id': 'id', 'attitudes_count': 'attitudes_count', 'comments_count': 'comments_count',
                        'reposts_count': 'reposts_count', 'picture': 'original_pic', 'pictures': 'pics',
                        'created_at': 'created_at', 'source': 'source', 'text': 'text', 'raw_text': 'raw_text',
                        'thumbnail': 'thumbnail_pic',
                    }
                    for field, attr in field_map.items():
                        weibo_item[field] = mblog.get(attr)
                    weibo_item['user'] = response.meta.get('uid')
                    #过滤保留了  （@用户名：） 后的内容，尽管某用户发表微博中@其他人的发言，但这有利于主题提取该用户所关注的事情
                    s2= re.sub('<.*','/',weibo_item['text'])#使用re过滤掉标签
                    # s2=re.sub('@.*?/','',s1)#对过滤掉标签的微博过滤掉@用户名
                    weibo_item['text']=re.sub('/+','',re.sub('(：+)',' / ',s2))
                    yield weibo_item
            # 下一页微博
            uid = response.meta.get('uid')
            page = response.meta.get('page') + 1
            yield Request(self.weibo_url.format(uid=uid, page=page), callback=self.parse_weibos,
                          meta={'uid': uid, 'page': page})

