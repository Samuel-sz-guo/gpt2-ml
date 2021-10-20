#! /usr/bin/python
# -*- coding: UTF-8 -*-
import requests
from pymysql_comm import UsingMysql
import time

def select_one(cursor):
    cursor.execute("select id from www_kaifamei_com_ecms_news order by id DESC limit 1;")
    data = cursor.fetchone()
    print("-- 单条记录: {0} ".format(data['id']))
    return data['id']

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
    #create_one('python测试3','正文3')
    data = '什么是区块链？借着区块链的热潮，相信你一定对这个概念不陌生。不过，今天我们不谈这个热词。我们先来简单解释一下区块链技术，以及它对金融行业的影', '响。“一言蔽之，区块链就是分布式数据存储、点对点传输、共识机制、加密算法等计算机技术的新型应用模式。”请你不要用这么抽象的语言来概括这个概念', '。从过去时来看，区块链技术就像区块链的代名词，是不同技术支撑起来的结果，它的优势在于去中心化和不可篡改。它的缺点是要求每个参与者都要有丰富的', '数据储备，要是都是纸面信息就没啥用了。不同的区块链技术原理，在适用方向上有区别。而简单粗暴的归纳，它们分为三类：1.比特币：去中心化，借助各', '大数字货币背后的加密算法，人人都可以建一个账本，然后所有的交易记录都能备份起来。每个参与者（比如小明）都可以给自己的账本各种签名，使得交易记', '录不可更改，从而有效防止黑客和恶意篡改交易记录。小明主要是维护账本和交易记录的安全性。2.以太坊：智能合约，人人都可以发行自己的代币。每个人', '都有一定的权限来管理自己账本上的交易，每笔交易都会有账本以及相应的代币记录，加上运营奖励和挖矿奖励的不断改进，节点越来越多，交易成本越来越低', '，所以出现以太币交易对的概率越来越大。参与方便，只要在以太坊节点上注册账户，就可以发布交易，也可以为账户充值或者购买eth以及其他任何东西。', '参与者也可以在自己账户和代币账本上注册账户，就可以为自己发布交易，还可以给账户充值或者购买代币。3.莱特币：使用ripplerabbit，后', '两者一个是区块链生态系统中的ripple（瑞波）rabbit，一个是社区的ripple（瑞波）。因为瑞波网络本身的安全性问题，所以莱特币比瑞', '波要稍逊一筹。你可以理解为，他们是通过类似比特币是中心化系统的方式来运行的，既保证了交易的安全，又保证了全网算力（相当于挖矿机器的算力）不平', '衡，让矿工大胆假设，小心求证，拥有更多算力的节点稳定整个网络。对于一般人而言，也许不大容易区分上面三种区块链技术，或者说，不太了解其原理，如', '果你从小看《射雕英雄传》武林盟主自打有了阴谋和江湖势力以后，不也一样杀人不眨眼么，最后被灭门吗。看到这里，应该对区块链有所了解了。其实，你大', '可不必把比特币和其他所有比特币都放在一起，从货币本身，比特币是建立在区块链技术之上的。当然，一般来说，大家会把比特币归类于区块链技术，或者说', '是区块链底层技术。这是因为在各种风口中，整个金融行业都在从区块链技术上寻找新的机会。但是，最有可能真正改变金融行业的，必然 '

    print(str(data).replace('。', '。\r\n  '))
    datas = ["https://zdfoundation.org/hq/1059.html","https://zdfoundation.org/hq/1060.html"]
    HEADERS_POST = {
        "User-Agent": "curl/7.12.1",
        "Host": "data.zz.baidu.com",
        "Content-Type": "text/plain",
        "Content-Length": "83"
    }
    r = requests.post('http://data.zz.baidu.com/urls?site=https://zdfoundation.org&token=vtgRi1g5lZcHBRfL', 'https://zdfoundation.org/hq/1059.html',headers=HEADERS_POST)
    print(r.text)
