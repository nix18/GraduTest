import datetime
from functools import singledispatch  # 通过第一个参数类型判断函数

import utils.sqlUtils as sql


# 验证token是否有效
@singledispatch
def verification_token(uid, token: str):
    try:
        sql.session.commit()
        store_token_list = sql.session.query(sql.user).filter(sql.user.uid == uid).first()
        if len(store_token_list.token) == 0:
            return -1
        if store_token_list.token == token:
            if datetime.datetime.now() < store_token_list.expire_time:
                print("用户id: " + str(uid) + " 登录验证成功" + str(datetime.datetime.now()))
                return uid
            else:
                sql.session.query(sql.user).filter(sql.user.uid == uid).delete()  # 删除无效token
                sql.session.commit()
        print("用户id: " + str(uid) + " 登录验证失败" + str(datetime.datetime.now()))
        return -1
    except:
        sql.session.rollback()
        print("用户id: " + str(uid) + " 登录验证失败" + str(datetime.datetime.now()))
        return -1


@verification_token.register(str)
def _verification_token(uname, token: str):
    try:
        sql.session.commit()
        store_token_list = sql.session.query(sql.user).filter(sql.user.user_name == uname).first()
        if len(store_token_list.token) == 0:
            return -1
        if store_token_list.token == token:
            if datetime.datetime.now() < store_token_list.expire_time:
                print("用户id: " + str(store_token_list.uid) + " 登录验证成功" + str(datetime.datetime.now()))
                return store_token_list.uid
            else:
                sql.session.query(sql.user).filter(
                    sql.user.uid == store_token_list.uid).delete()  # 删除无效token
                sql.session.commit()
        print("用户名： " + uname + " 登录验证失败" + str(datetime.datetime.now()))
        return -1
    except:
        sql.session.rollback()
        print("用户名： " + uname + " 登录验证失败" + str(datetime.datetime.now()))
        return -1
