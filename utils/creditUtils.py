import random
import traceback

import utils.sqlUtils as sql
import datetime


# TODO creditConsume 扣完后不能为负
def creditAdd(uid: int, creditnum: int, creditdesc: str):
    try:
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
    except:
        traceback.print_exc()
        sql.session.rollback()


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
    try:
        new_creditdetail = sql.creditdetail(
            uid=uid, creditnum=creditnum, creditdesc=creditdesc, ctime=ctime)
        sql.session.add(new_creditdetail)
        sql.session.commit()
        return 1
    except:
        traceback.print_exc()
        sql.session.rollback()


def getCredit(uid: int):
    try:
        sql.session.commit()
        return sql.session.query(sql.credit.creditsum).filter(sql.credit.uid == uid).first()
    except:
        traceback.print_exc()
        sql.session.rollback()


def operateCreditlotsum(uid: int, type: int):
    """
    小保底计数操作
    :param uid:
    :param type: 操作类型 0 查询 1 置零
    :return:
    """
    try:
        if type == 0:
            sql.session.commit()
            return sql.session.query(sql.credit.lotterysum).filter(sql.credit.uid == uid).first()
        if type == 1:
            ret = sql.session.query(sql.credit).filter(sql.credit.uid == uid).update(
                {sql.credit.lotterysum: 0},
                synchronize_session=False)
            sql.session.commit()
            return ret
    except:
        traceback.print_exc()
        sql.session.rollback()


def operateCreditlotSsum(uid: int, type: int):
    """
    大保底计数操作
    :param uid:
    :param type: 操作类型 0 查询 1 置零
    :return:
    """
    try:
        if type == 0:
            sql.session.commit()
            return sql.session.query(sql.credit.lotterySsum).filter(sql.credit.uid == uid).first()
        if type == 1:
            ret = sql.session.query(sql.credit).filter(sql.credit.uid == uid).update(
                {sql.credit.lotterySsum: 0},
                synchronize_session=False)
            sql.session.commit()
            return ret
    except:
        traceback.print_exc()
        sql.session.rollback()


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
    # 生成抽奖结果
    index = weighted_random([('Gold', 0.6), ('Silver', 5.1), ('Bronze', 94.3)])
    if operateCreditlotsum(uid, 0)[0] + 1 >= 10:
        index = 'Silver'
    if operateCreditlotSsum(uid, 0)[0] + 1 >= 90:
        index = 'Gold'
    # 将大小保底计数+1
    global ret1
    try:
        ret1 = sql.session.query(sql.credit).filter(sql.credit.uid == uid).update(
            {sql.credit.lotterysum: sql.credit.lotterysum + 1, sql.credit.lotterySsum: sql.credit.lotterySsum + 1},
            synchronize_session=False)
        sql.session.commit()
    except:
        traceback.print_exc()
        sql.session.rollback()
    # 消耗积分，记录结果
    ret2 = creditConsume(uid, 10, "积分抽奖，结果：" + index)
    # 若上两步任一步不成功，返回错误
    if ret1 + ret2 != 2:
        return 0
    # 若保底，重置保底次数
    if index == 'Silver':
        operateCreditlotsum(uid, 1)
    if index == 'Gold':
        operateCreditlotSsum(uid, 1)
    return index


# FIXME sql次数过多
# TODO 中奖记录 临时使用积分记录表记录抽奖记录
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
