import uvicorn
from fastapi import FastAPI
import datetime
import utils.sqlUtils as sql
import utils.veriToken as veriToken
import hashlib
import traceback
import os

app = FastAPI()

# 公用变量
adminMail = "admin@admin.com"


@app.get("/")
async def read_root():
    return {"Hello": "Test"}


# 查询
@app.get("/query")
async def query(uid: int, token: str):
    if veriToken.verificationToken(uid, token):
        pass
    else:
        return {"Error": "Login Expired"}
    qd_list = []
    qd = sql.session.query(sql.qiandao).all()
    sql.session.close()
    for i in range(len(qd)):
        qd_list.append(
            {
                'qd_id': qd[i].qd_id,
                'uid': qd[i].uid,
                'qd_time': qd[i].qd_time,
            }
        )
    return qd_list


# 注册
@app.post("/register")
async def register(uname: str, uprofile: str, upwd: str):
    try:
        isnameexist = sql.session.query(sql.user.uname).filter(sql.user.uname == uname).first() is not None
        if isnameexist:
            return {"Error": "Name Exists"}
        else:
            # 密码加密处理在客户端
            new_user = sql.user(uname=uname, uprofile=uprofile, upwd=upwd)
            sql.session.add(new_user)
            sql.session.commit()
            return {"Msg": "Register Success"}
    except Exception as e:
        return {"Error": "Sql Error , Pls Contact: " + adminMail + "reason: " + str(e)}


# 登录
@app.post("/login")
async def login(uname: str, upwd: str):
    cuser = sql.session.query(sql.user).filter(sql.user.uname == uname).first()
    # 判空
    if cuser is None:
        return {"Error": "Login Failed"}
    cpwd = cuser.upwd
    cuid = cuser.uid
    if upwd == cpwd:  # 验证账号密码
        isexist = sql.session.query(sql.tokenList.token).filter(sql.tokenList.uid == cuid).first()
        timenext = datetime.datetime.now() + datetime.timedelta(days=3)
        token = hashlib.sha1(os.urandom(32)).hexdigest()
        if isexist is None:
            new_token = sql.tokenList(uid=cuid, token=token,
                                      expire_time=timenext)
            sql.session.add(new_token)
        else:
            sql.session.query(sql.tokenList).filter(sql.tokenList.uid == cuid) \
                .update({"token": token, "expire_time": timenext})
        sql.session.commit()
        return {"Token": token}
    else:
        return {"Error": "Login Failed"}


# 签到
@app.get("/qiandao")
async def qiandao(uname: str, token: str):
    try:
        stokenlist = sql.session.query(sql.tokenList) \
            .join(sql.user, sql.tokenList.uid == sql.user.uid).filter(sql.user.uname == uname).first()
        if stokenlist is not None:
            if stokenlist.token == token and datetime.datetime.now() < stokenlist.expire_time:
                new_qd = sql.qiandao(uid=stokenlist.uid, qd_time=datetime.datetime.now())
                sql.session.add(new_qd)
                sql.session.commit()
                return {"Msg": "签到成功"}
        return {"Msg": "签到失败，凭据出错"}
    except Exception:
        traceback.print_exc()
        return {"Msg": "签到失败，服务器内部错误"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}


if __name__ == '__main__':
    uvicorn.run(app='main:app', host="127.0.0.1", port=8000, reload=True, debug=True)
