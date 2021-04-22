import datetime
import json
import os
from time import localtime, time, strftime, sleep
from typing import List

from alibabacloud_dm20151123 import models as dm_20151123_models
from alibabacloud_dm20151123.client import Client as Dm20151123Client
from alibabacloud_tea_openapi import models as open_api_models

import utils.sqlUtils as sql


class Reminder:
    def __init__(self):
        pass

    @staticmethod
    def create_client(
            access_key_id: str,
            access_key_secret: str,
    ) -> Dm20151123Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 您的AccessKey ID,
            access_key_id=access_key_id,
            # 您的AccessKey Secret,
            access_key_secret=access_key_secret
        )
        # 访问的域名
        config.endpoint = 'dm.aliyuncs.com'
        return Dm20151123Client(config)

    @staticmethod
    def main(
            args: List[str],
    ) -> None:
        client = Reminder.create_client('LTAI5tGAJeb5qLtMsHgTcDFc', 'phgzqC8MIkQmUq6EyMkFCNrc8w4KC0')
        single_send_mail_request = dm_20151123_models.SingleSendMailRequest(
            account_name='goodhabitsys@mail.upfun.xyz',
            address_type=1,
            tag_name=args[0],
            reply_to_address=True,
            to_address=args[1],
            subject=args[2],
            html_body=args[3],
            text_body=args[4],
            from_alias='好习惯养成系统',
            reply_address='admin@moecola.com',
            reply_address_alias='好习惯养成系统'
        )
        # 复制代码运行请自行打印 API 的返回值
        ret = client.single_send_mail(single_send_mail_request)
        print("发信结果 " + ret.to_map()['body']['EnvId'])

    @staticmethod
    async def main_async(
            args: List[str],
    ) -> None:
        client = Reminder.create_client('LTAI5tGAJeb5qLtMsHgTcDFc', 'phgzqC8MIkQmUq6EyMkFCNrc8w4KC0')
        single_send_mail_request = dm_20151123_models.SingleSendMailRequest(
            account_name='goodhabitsys@mail.upfun.xyz',
            address_type=1,
            tag_name=args[0],
            reply_to_address=True,
            to_address=args[1],
            subject=args[2],
            html_body=args[3],
            text_body=args[4],
            from_alias='好习惯养成系统',
            reply_address='admin@moecola.com',
            reply_address_alias='好习惯养成系统'
        )
        # 复制代码运行请自行打印 API 的返回值
        await client.single_send_mail_async(single_send_mail_request)


def datetimestrptime(time_string, time_fmt):
    return datetime.datetime.strptime(time_string, time_fmt)


def remind(send: bool):
    sql.session.commit()
    wx_running_habits = sql.session.query(sql.running_habits).filter(sql.running_habits.target_days == 0).all()
    for habits in wx_running_habits:
        config_dict = json.loads(habits.user_config)
        week_now = localtime(time())
        week_day = strftime("%a", week_now)
        week_day = week_day[0:2].upper()
        now = datetime.date.today()
        if config_dict['start_time'] <= str(now) <= config_dict['end_time']:
            if week_day in config_dict['remind_days_str']:
                remind_time = datetimestrptime(config_dict['remind_time'], "%H:%M")
                now_time = datetimestrptime(strftime("%H:%M", localtime()), "%H:%M")
                delta = now_time - remind_time
                if delta.seconds < 181:
                    wx_user_mail = sql.session.query(sql.user.user_profile).filter(sql.user.uid == habits.uid).first()[
                        0]
                    habit_data = sql.session.query(sql.good_habits).filter(sql.good_habits.hid == habits.hid).first()
                    if (send):
                        Reminder.main(["好习惯养成提醒", wx_user_mail, "好习惯养成提醒: " + habit_data.habit_name,
                                       habit_data.habit_content, habit_data.habit_content])
                    else:
                        print(strftime("%Y-%m-%d %H:%M:%S",
                                       localtime()) + " 模拟发信提醒: " + habit_data.habit_name + "  " + wx_user_mail)


def worker(interval: int, send: bool):
    print("邮件提醒子进程 [%s]" % os.getpid())
    while True:
        remind(send)
        sleep(interval)
