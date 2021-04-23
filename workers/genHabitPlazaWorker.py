import datetime
import os
import time

import utils.sqlUtils as sql


# TODO 好习惯top10生成 根据热度habit_heat每小时1次更新

def gen(interval: int, log: bool):
    """
    interval: 更新间隔时间（秒）
    log: 是否开启命令行日志
    """
    print("习惯广场子进程 [%s]" % os.getpid())
    while True:
        if log is True:
            print("已更新习惯广场 " + str(datetime.datetime.now()))
        top10 = sql.session.query(sql.good_habits).filter(sql.good_habits.habit_isvisible == True).order_by(
            sql.good_habits.habit_heat.desc()).limit(10).all()
        sql.session.query(sql.habit_plaza).delete()
        for items in top10:
            new_item = sql.habit_plaza(hid=items.hid, create_uid=items.create_uid, habit_name=items.habit_name,
                                       habit_content=items.habit_content, habit_category=items.habit_category,
                                       habit_heat=items.habit_heat, habit_create_time=items.habit_create_time)
            sql.session.add(new_item)
        sql.session.commit()
        time.sleep(interval)
