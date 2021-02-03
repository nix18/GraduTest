import utils.sqlUtils as sql
import datetime
from functools import singledispatch  # 通过第一个参数类型判断函数


# 验证token是否有效
@singledispatch
def verificationToken(uid, token: str):
    store_token_list = sql.session.query(sql.tokenList).filter(sql.tokenList.uid == uid).first()
    try:
        if store_token_list.token == token and datetime.datetime.now() < store_token_list.expire_time:
            print("用户id: " + str(uid) + " 登录验证成功")
            return uid
        else:
            print("用户id: " + str(uid) + " 登录验证失败")
            return -1
    except:
        print("用户id: " + str(uid) + " 登录验证失败")
        return -1


@verificationToken.register(str)
def _verificationToken(uname, token: str):
    stokenlist = sql.session.query(sql.tokenList) \
        .join(sql.user, sql.tokenList.uid == sql.user.uid).filter(sql.user.uname == uname).first()
    try:
        if stokenlist.token == token and datetime.datetime.now() < stokenlist.expire_time:
            print("用户id: " + str(stokenlist.uid) + " 登录验证成功")
            return stokenlist.uid
        else:
            print("用户名： " + uname + " 登录验证失败")
            return -1
    except:
        print("用户名： " + uname + " 登录验证失败")
        return -1
