import random

import utils.sqlUtils as sql
import datetime


# TODO creditConsume 扣完后不能为负
def creditAdd(uid: int, creditnum: int, creditdesc: str):
    ret = sql.session.query(sql.credit).filter(sql.credit.uid == uid) \
        .update({sql.credit.creditsum: sql.credit.creditsum + creditnum}, synchronize_session=False)
    creditDetail(uid, creditnum, creditdesc, datetime.datetime.now())
    sql.session.commit()
    if ret == 1:
        return 1
    else:
        isexist = sql.session.query(sql.credit).filter(sql.credit.uid == uid).first()
        if isexist is None:
            new_credit = sql.credit(uid=uid, creditsum=creditnum)
            sql.session.add(new_credit)
            sql.session.commit()
            return 1
        return 0


# TODO
# 积分记录
def creditDetail(uid: int, creditnum: int, creditdesc: str, ctime: datetime.datetime):
    new_creditdetail = sql.creditdetail(
        uid=uid, creditnum=creditnum, creditdesc=creditdesc, ctime=ctime)
    sql.session.add(new_creditdetail)
    sql.session.commit()
    return 1


def getCredit(uid: int):
    return sql.session.query(sql.credit.creditsum).filter(sql.credit.uid == uid).first()


def weighted_random(items):
    global x
    total = sum(w for _, w in items)
    n = random.uniform(0, total)  # 在饼图扔骰子
    for x, w in items:  # 遍历找出骰子所在的区间
        if n < w:
            break
        n -= w
    return x


# 单次抽奖
def creditLottery(uid: int):
    ret = creditAdd(uid, -10, "积分抽奖")
    if ret == 1:
        index = weighted_random([('Gold', 0.6), ('Silver', 5.1), ('Bronze', 94.3)])
        return index
    else:
        return 0


def creditLotteryDuo(uid: int, count: int):
    global flag
    flag = 0
    retsum = []
    for i in range(count):
        ret = creditLottery(uid)
        if ret == "Silver":
            flag = 1
        if (i + 1) % 10 == 0 and flag == 0:
            ret = "Silver"
        retsum.append(ret)
    flag = 0
    return retsum
