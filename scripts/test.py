#! /usr/bin/python
# -*- coding: UTF-8 -*-
import re

import requests
from pymysql_comm import UsingMysql
import time

def select_one(cursor):
    cursor.execute("select id from www_kaifamei_com_ecms_news order by id DESC limit 1;")
    data = cursor.fetchone()
    print("-- 单条记录: {0} ".format(data['id']))
    return data['id']

def select_one_keyword(cursor):
    cursor.execute("select keyword from key_20202")
    data = cursor.fetchall()
    print("取出:")
    return data

# 新增单条记录
def create_one(title,newstText):

    with UsingMysql(log_time=True) as um:
        id = select_one(um.cursor)+1
        times = time.strftime('%Y-%m-%d', time.localtime())
        timelangs = time.time()
        print(timelangs)
        sql = "INSERT INTO glc_x.www_kaifamei_com_ecms_news (id, classid, ttid, onclick, plnum, totaldown, newspath, filename, userid, username, firsttitle, isgood, ispic, istop, isqf, ismember, isurl, truetime, lastdotime, havehtml, groupid, userfen, titlefont, titleurl, stb, fstb, restb, keyboard, title, newstime, titlepic, eckuid, ftitle, smalltext, diggtop) VALUES (%s, 16, 0, 2, 0, 0, '', %s, 1, 'kaifamei', 0, 0, 0, 0, 0, 0, 0, %s, %s, 1, 0, 0, '', '/hq/new/%s.html', 1, 1, 1, '', %s, %s, '', 0, %s, '测试简介2', 0);"
        prams = (id,id,timelangs,timelangs,id,title,timelangs,title)
        um.cursor.execute(sql,prams)
        #data
        sqlData= "INSERT INTO glc_x.www_kaifamei_com_ecms_news_data_1 (id, classid, keyid, dokey, newstempid, closepl, haveaddfen, infotags, writer, befrom, newstext) VALUES (%s, 16, '', 1, 0, 0, 0, '区块链', '', '', %s);"
        prams = (id, newstText)
        um.cursor.execute(sqlData, prams)
        #Index
        sqlIndex= "INSERT INTO glc_x.www_kaifamei_com_ecms_news_index (id, classid, checked, newstime, truetime, lastdotime, havehtml) VALUES (%s, 16, 1, %s, %s, %s, 1);"
        prams = (id, timelangs,timelangs,timelangs)
        um.cursor.execute(sqlIndex, prams)

if __name__ == '__main__':
    cont='小米集团股票股吧里总能看到一些无聊的问题，要举报就直接举报。反正米酒不是米8。不知道有人为啥要这么无聊[SEP]可以入手。具体见小米公司对其'
    print(re.search('(.*)+。',cont).group(0))


