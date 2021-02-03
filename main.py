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
    if veriToken.verificationToken(uid, token) != -1:
        pass
    else:
        return {"Error": "登陆错误"}
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
            return {"Msg": "注册成功"}
    except:
        traceback.print_exc()
        return {"Error": "数据库错误 , 请联系: " + adminMail}


# 登录
@app.post("/login")
async def login(uname: str, upwd: str):
    cuser = sql.session.query(sql.user).filter(sql.user.uname == uname).first()
    # 判空
    if cuser is None:
        return {"Error": "登录失败"}
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
        return {"Error": "登录失败"}


# 签到
@app.get("/qiandao")
async def qiandao(uname: str, token: str):
    try:
        cuid = veriToken.verificationToken(uname, token)
        if cuid != -1:
            new_qd = sql.qiandao(uid=cuid, qd_time=datetime.datetime.now())
            sql.session.add(new_qd)
            sql.session.commit()
            return {"Msg": "签到成功"}
        return {"Error": "签到失败，凭据出错"}
    except:
        traceback.print_exc()
        return {"Error": "签到失败，服务器内部错误"}


# 添加好习惯
@app.post("/addhabit")
async def add_habit(uid: int, token: str, hname: str, hcontent: str, hcategory: str = None):
    cuid = veriToken.verificationToken(uid, token)
    try:
        if cuid != -1:
            new_habit = sql.goodHabits(cuid=cuid, hname=hname, hcontent=hcontent,
                                       hcategory=hcategory, htime=datetime.datetime.now())
            sql.session.add(new_habit)
            sql.session.commit()
            return {"Msg": "习惯添加成功"}
        else:
            return {"Error": "习惯添加失败，凭据失效"}
    except:
        return {"Error": "习惯添加失败，服务器内部错误"}


# 查询好习惯 f'{hname}'为格式化字符串，注意引号
@app.get("/selhabits")
async def sel_habit(hname: str = None, hcategory: str = None):
    if hname is None:
        if hcategory is None:
            habits = sql.session.query(sql.goodHabits).all()
        else:
            habits = sql.session.query(sql.goodHabits).filter(sql.goodHabits.hcategory.like(f'%{hcategory}%')).all()
    else:
        if hcategory is None:
            habits = sql.session.query(sql.goodHabits).filter(sql.goodHabits.hname.like(f'%{hname}%')).all()
        else:
            habits = sql.session.query(sql.goodHabits).filter(
                sql.goodHabits.hname.like(f'%{hname}%'), sql.goodHabits.hcategory.like(f'%{hcategory}%')).all()
    return habits


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}


if __name__ == '__main__':
    uvicorn.run(app='main:app', host="127.0.0.1", port=8000, reload=True, debug=True)
