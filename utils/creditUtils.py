import random
import traceback

import utils.sqlUtils as sql
import datetime


def credit_add(uid: int, creditnum: int, creditdesc: str):
    try:
        ret = sql.session.query(sql.credit).filter(sql.credit.uid == uid) \
            .update({sql.credit.credit_sum: sql.credit.credit_sum + creditnum}, synchronize_session=False)
        credit_detail(uid, creditnum, creditdesc, datetime.datetime.now())
        sql.session.commit()
        if ret == 1:
            return 0
        else:
            isexist = sql.session.query(sql.credit).filter(sql.credit.uid == uid).first()
            if isexist is None:
                new_credit = sql.credit(uid=uid, credit_sum=creditnum)
                sql.session.add(new_credit)
                sql.session.commit()
                return 0
            return -1
    except:
        traceback.print_exc()
        sql.session.rollback()
        return -1


def credit_consume(uid: int, creditnum: int, creditdesc: str):
    num = get_credit(uid)
    if num is None:
        credit_add(uid, 0, "积分初始化")
        num = [0]
    if creditnum > num[0]:
        return -1
    return credit_add(uid, -creditnum, creditdesc)


# 积分记录
def credit_detail(uid: int, creditnum: int, creditdesc: str, ctime: datetime.datetime):
    try:
        new_credit_detail = sql.credit_detail(
            uid=uid, credit_num=creditnum, credit_desc=creditdesc, credit_time=ctime)
        sql.session.add(new_credit_detail)
        sql.session.commit()
        return 0
    except:
        traceback.print_exc()
        sql.session.rollback()
        return -1


def get_credit(uid: int):
    try:
        sql.session.commit()
        return sql.session.query(sql.credit.credit_sum).filter(sql.credit.uid == uid).first()
    except:
        traceback.print_exc()
        sql.session.rollback()
        return -1


def operate_credit_lottery_sum(uid: int, type: int):
    """
    小保底计数操作
    :param uid:
    :param type: 操作类型 0 查询 1 置零
    :return:
    """
    try:
        if type == 0:
            sql.session.commit()
            return sql.session.query(sql.credit.lottery_sum).filter(sql.credit.uid == uid).first()
        if type == 1:
            ret = sql.session.query(sql.credit).filter(sql.credit.uid == uid).update(
                {sql.credit.lottery_sum: 0},
                synchronize_session=False)
            sql.session.commit()
            return ret
    except:
        traceback.print_exc()
        sql.session.rollback()


def operate_credit_lottery_Ssum(uid: int, type: int):
    """
    大保底计数操作
    :param uid:
    :param type: 操作类型 0 查询 1 置零
    :return:
    """
    try:
        if type == 0:
            sql.session.commit()
            return sql.session.query(sql.credit.lottery_Ssum).filter(sql.credit.uid == uid).first()
        if type == 1:
            ret = sql.session.query(sql.credit).filter(sql.credit.uid == uid).update(
                {sql.credit.lottery_Ssum: 0},
                synchronize_session=False)
            sql.session.commit()
            return ret
    except:
        traceback.print_exc()
        sql.session.rollback()


# 计算返还积分倍率
def cal_multiple(target_days: int, capital: int):
    if capital < 100 or target_days < 7:
        multiple = 1.5
    elif capital < 300 or target_days < 14:
        multiple = 2
    elif capital < 600 or target_days < 21:
        multiple = 2.5
    else:
        multiple = 3
    return multiple


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
def credit_lottery(uid: int):
    # 生成抽奖结果
    index = weighted_random([('Gold', 0.6), ('Silver', 5.1), ('Bronze', 94.3)])
    if operate_credit_lottery_sum(uid, 0)[0] + 1 >= 10:
        index = 'Silver'
    if operate_credit_lottery_Ssum(uid, 0)[0] + 1 >= 90:
        index = 'Gold'
    # 将大小保底计数+1
    global ret1
    try:
        ret1 = sql.session.query(sql.credit).filter(sql.credit.uid == uid).update(
            {sql.credit.lottery_sum: sql.credit.lottery_sum + 1, sql.credit.lottery_Ssum: sql.credit.lottery_Ssum + 1},
            synchronize_session=False)
        sql.session.commit()
    except:
        traceback.print_exc()
        sql.session.rollback()
    # 消耗积分，记录结果
    ret2 = credit_consume(uid, 10, "积分抽奖，结果：" + index)
    # 若上两步任一步不成功，返回错误
    if ret1 + ret2 != 1:
        return -1
    # 若保底，重置保底次数
    if index == 'Silver':
        operate_credit_lottery_sum(uid, 1)
    if index == 'Gold':
        operate_credit_lottery_Ssum(uid, 1)
    return index


# FIXME sql次数过多
# 中奖记录 临时使用积分记录表记录抽奖记录
def credit_lottery_duo(uid: int, count: int):
    num = get_credit(uid)
    if num is None:
        num = [0]
    if count * 10 > num[0]:  # 确认积分是否足够
        return []
    ret_sum = []
    for i in range(count):
        ret = credit_lottery(uid)
        if ret == -1:
            return ret_sum
        ret_sum.append(ret)
    return ret_sum
