import datetime
import os
import time

import schedule as schedule
from sqlalchemy import cast, DATE

import utils.sqlUtils as sql

'''
每天{{t}}时运行，检查APP用户（非微信用户）当天积分记录，匹配行为按规则得出user_score
签到：+10分
习惯打卡：+20分
抽奖1次：+5分
购买好习惯：+50分
放弃好习惯：-60分
'''


def gen(t: str, log: bool):
    print("用户等级子进程 [%s]" % os.getpid())
    print("每天 " + t + " 更新用户等级积分")
    schedule.every().day.at(t).do(job, log)
    while True:
        schedule.run_pending()
        time.sleep(1)


def job(log: bool):
    if log:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " 开始更新用户等级积分")
    sql.session.commit()
    now = datetime.date.today()
    users = sql.session.query(sql.user.uid).filter(sql.user.user_name.notlike("WX_%")).all()
    for u in users:
        notes = sql.session.query(sql.credit_detail).filter(sql.credit_detail.uid == u[0]
                                                            , cast(sql.credit_detail.credit_time, DATE) == now
                                                            ).all()
        for note in notes:
            if "签到" in note.credit_desc:
                modScore(u[0], 10)
            if "习惯打卡" in note.credit_desc:
                modScore(u[0], 20)
            if "抽奖" in note.credit_desc:
                modScore(u[0], 5)
            if "购买" in note.credit_desc:
                modScore(u[0], 50)
            if "放弃" in note.credit_desc:
                modScore(u[0], -60)
    if log:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " 完成更新用户等级积分")


def modScore(uid: int, val: int):
    sql.session.commit()
    sql.session.query(sql.user).filter(sql.user.uid == uid).update(
        {sql.user.user_score: sql.user.user_score + val})
    sql.session.commit()
