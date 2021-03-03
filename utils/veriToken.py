import utils.sqlUtils as sql
import datetime
from functools import singledispatch  # 通过第一个参数类型判断函数
import traceback


# 验证token是否有效
@singledispatch
def verificationToken(uid, token: str):
    try:
        store_token_list = sql.session.query(sql.tokenList).filter(sql.tokenList.uid == uid).first()
        if store_token_list.token == token:
            if datetime.datetime.now() < store_token_list.expire_time:
                print("用户id: " + str(uid) + " 登录验证成功")
                return uid
            else:
                sql.session.query(sql.tokenList).filter(sql.tokenList.uid == uid).delete()  # 删除无效token
                sql.session.commit()
        print("用户id: " + str(uid) + " 登录验证失败")
        return -1
    except:
        sql.session.rollback()
        print("用户id: " + str(uid) + " 登录验证失败")
        return -1


@verificationToken.register(str)
def _verificationToken(uname, token: str):
    try:
        stokenlist = sql.session.query(sql.tokenList) \
            .join(sql.user, sql.tokenList.uid == sql.user.uid).filter(sql.user.uname == uname).first()
        if stokenlist.token == token:
            if datetime.datetime.now() < stokenlist.expire_time:
                print("用户id: " + str(stokenlist.uid) + " 登录验证成功")
                return stokenlist.uid
            else:
                sql.session.query(sql.tokenList).filter(sql.tokenList.uid == stokenlist.uid).delete()  # 删除无效token
                sql.session.commit()
        print("用户名： " + uname + " 登录验证失败")
        return -1
    except:
        sql.session.rollback()
        print("用户名： " + uname + " 登录验证失败")
        return -1
