import utils.sqlUtils as sql
import datetime


# 验证token是否有效
def verificationToken(uid: int, token: str):
    store_token_list = sql.session.query(sql.tokenList).filter(sql.tokenList.uid == uid).first()
    try:
        if store_token_list.token == token and datetime.datetime.now() < store_token_list.expire_time:
            print("登录验证成功")
            return True
        else:
            print("登录验证失败")
            return False
    except:
        print("登录验证失败")
        return False
