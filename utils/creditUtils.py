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


def creditConsume(uid: int, creditnum: int, creditdesc: str):
    num = getCredit(uid)
    if num is None:
        creditAdd(uid, 0, "积分初始化")
        num = [0]
    if creditnum > num[0]:
        return 0
    return creditAdd(uid, -creditnum, creditdesc)


# TODO
# 积分记录
def creditDetail(uid: int, creditnum: int, creditdesc: str, ctime: datetime.datetime):
    new_creditdetail = sql.creditdetail(
        uid=uid, creditnum=creditnum, creditdesc=creditdesc, ctime=ctime)
    sql.session.add(new_creditdetail)
    sql.session.commit()
    return 1


def getCredit(uid: int):
    sql.session.commit()
    return sql.session.query(sql.credit.creditsum).filter(sql.credit.uid == uid).first()


def operateCreditlotsum(uid: int, type: int):
    """
    小保底计数操作
    :param uid:
    :param type: 操作类型 0 查询 1 置零
    :return:
    """
    if type == 0:
        sql.session.commit()
        return sql.session.query(sql.credit.lotterysum).filter(sql.credit.uid == uid).first()
    if type == 1:
        ret = sql.session.query(sql.credit).filter(sql.credit.uid == uid).update(
            {sql.credit.lotterysum: 0},
            synchronize_session=False)
        sql.session.commit()
        return ret


def operateCreditlotSsum(uid: int, type: int):
    """
    大保底计数操作
    :param uid:
    :param type: 操作类型 0 查询 1 置零
    :return:
    """
    if type == 0:
        sql.session.commit()
        return sql.session.query(sql.credit.lotterySsum).filter(sql.credit.uid == uid).first()
    if type == 1:
        ret = sql.session.query(sql.credit).filter(sql.credit.uid == uid).update(
            {sql.credit.lotterySsum: 0},
            synchronize_session=False)
        sql.session.commit()
        return ret


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
    ret = creditConsume(uid, 10, "积分抽奖")
    if ret == 1:
        ret1 = sql.session.query(sql.credit).filter(sql.credit.uid == uid).update(
            {sql.credit.lotterysum: sql.credit.lotterysum + 1, sql.credit.lotterySsum: sql.credit.lotterySsum + 1},
            synchronize_session=False)  # 抽奖时首先将大小保底计数+1
        sql.session.commit()
        if ret1 == 0:
            return 0
        index = weighted_random([('Gold', 0.6), ('Silver', 5.1), ('Bronze', 94.3)])
        if operateCreditlotsum(uid, 0)[0] >= 10:
            index = 'Silver'
        if operateCreditlotSsum(uid, 0)[0] >= 90:
            index = 'Gold'
        if index == 'Silver':
            operateCreditlotsum(uid, 1)
        if index == 'Gold':
            operateCreditlotSsum(uid, 1)
        return index
    else:
        return 0


def creditLotteryDuo(uid: int, count: int):
    num = getCredit(uid)
    if num is None:
        num = [0]
    if count * 10 > num[0]:  # 确认积分是否足够
        return []
    retsum = []
    for i in range(count):
        ret = creditLottery(uid)
        if ret == 0:
            return retsum
        retsum.append(ret)
    return retsum
