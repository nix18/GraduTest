import utils.sqlUtils as sql
import datetime
from functools import singledispatch  # 通过第一个参数类型判断函数
import traceback


# 验证token是否有效
@singledispatch
def verification_token(uid, token: str):
    try:
        store_token_list = sql.session.query(sql.token_list).filter(sql.token_list.uid == uid).first()
        if store_token_list.token == token:
            if datetime.datetime.now() < store_token_list.expire_time:
                print("用户id: " + str(uid) + " 登录验证成功")
                return uid
            else:
                sql.session.query(sql.token_list).filter(sql.token_list.uid == uid).delete()  # 删除无效token
                sql.session.commit()
        print("用户id: " + str(uid) + " 登录验证失败")
        return -1
    except:
        sql.session.rollback()
        print("用户id: " + str(uid) + " 登录验证失败")
        return -1


@verification_token.register(str)
def _verification_token(uname, token: str):
    try:
        store_token_list = sql.session.query(sql.token_list) \
            .join(sql.user, sql.token_list.uid == sql.user.uid).filter(sql.user.user_name == uname).first()
        if store_token_list.token == token:
            if datetime.datetime.now() < store_token_list.expire_time:
                print("用户id: " + str(store_token_list.uid) + " 登录验证成功")
                return store_token_list.uid
            else:
                sql.session.query(sql.token_list).filter(
                    sql.token_list.uid == store_token_list.uid).delete()  # 删除无效token
                sql.session.commit()
        print("用户名： " + uname + " 登录验证失败")
        return -1
    except:
        sql.session.rollback()
        print("用户名： " + uname + " 登录验证失败")
        return -1
