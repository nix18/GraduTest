import datetime
import os
import time
from threading import Thread


# TODO 好习惯top10生成 根据热度habit_heat每小时1次更新
class gen_habit_plaza(Thread):
    def __init__(self):
        super().__init__()
        print("习惯广场线程已初始化")

    def run(self):
        while True:
            # print("已更新习惯广场 " + str(datetime.datetime.now()))
            time.sleep(10)
