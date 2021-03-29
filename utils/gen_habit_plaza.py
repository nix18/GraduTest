import datetime
import time
from threading import Thread
import utils.sqlUtils as sql


# TODO 好习惯top10生成 根据热度habit_heat每小时1次更新
class gen_habit_plaza(Thread):
    def __init__(self):
        super().__init__()
        print("习惯广场线程已初始化")

    # TODO 监控表变动更新习惯广场
    def run(self):
        while True:
            print("已更新习惯广场 " + str(datetime.datetime.now()))
            top10 = sql.session.query(sql.good_habits).order_by(sql.good_habits.habit_heat.desc()).limit(10).all()
            sql.session.query(sql.habit_plaza).delete()
            for items in top10:
                new_item = sql.habit_plaza(hid=items.hid, create_uid=items.create_uid, habit_name=items.habit_name,
                                           habit_content=items.habit_content, habit_category=items.habit_category,
                                           habit_heat=items.habit_heat, habit_create_time=items.habit_create_time)
                sql.session.add(new_item)
            sql.session.commit()
            time.sleep(30)
