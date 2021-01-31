import uvicorn
from fastapi import FastAPI
import datetime
import utils.sqlUtils as sql
import utils.veriToken as veriToken
import hashlib
import os

app = FastAPI()


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


# 登录
@app.get("/login")
async def login(uid: int):
    isexist = sql.session.query(sql.tokenList.token).filter(sql.tokenList.uid == uid).first()
    token = hashlib.sha1(os.urandom(32)).hexdigest()
    timenext = datetime.datetime.now() + datetime.timedelta(days=3)
    if uid == 123:  # 验证账号密码
        if isexist is None:
            new_token = sql.tokenList(uid=uid, token=token,
                                      expire_time=timenext)
            sql.session.add(new_token)
        else:
            sql.session.query(sql.tokenList).filter(sql.tokenList.uid == uid) \
                .update({"token": token, "expire_time": timenext})
        sql.session.commit()
        return {"Token": token}
    else:
        return {"Error": "Login Failed"}


# 签到
@app.get("/qiandao")
async def qiandao(uid: int):
    try:
        new_qd = sql.qiandao(uid=uid, qd_time=datetime.datetime.now())
        sql.session.add(new_qd)
        sql.session.commit()
    except:
        return {"out": False}
    else:
        return {"out": True}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}


if __name__ == '__main__':
    uvicorn.run(app='main:app', host="127.0.0.1", port=8000, reload=True, debug=True)
