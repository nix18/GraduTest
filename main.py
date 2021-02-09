import uvicorn
from fastapi import FastAPI
import datetime
import utils.sqlUtils as sql
import utils.creditUtils as credit
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
        return {"Error": "登陆错误，凭据失效"}
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
            return {"Error": "名称已存在"}
        else:
            # 密码加密处理在客户端
            new_user = sql.user(uname=uname, uprofile=uprofile, upwd=upwd)
            sql.session.add(new_user)
            sql.session.commit()
            return {"Msg": "注册成功"}
    except:
        traceback.print_exc()
        return {"Error": "注册失败，服务器内部错误" + " 请联系: " + adminMail}


# 登录
@app.post("/login")
async def login(uname: str, upwd: str):
    try:
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
            return {"Uid": cuid, "Token": token}
        else:
            return {"Error": "登录失败"}
    except:
        traceback.print_exc()
        return {"Error": "登录失败，服务器内部错误" + " 请联系: " + adminMail}


# 签到
@app.post("/qiandao")
async def qiandao(uname: str, token: str):
    try:
        cuid = veriToken.verificationToken(uname, token)
        if cuid != -1:
            new_qd = sql.qiandao(uid=cuid, qd_time=datetime.datetime.now())
            sql.session.add(new_qd)
            if credit.creditAdd(cuid, 10) == 1:
                sql.session.commit()
                return {"Msg": "签到成功，积分+10"}
            else:
                raise Exception
        return {"Error": "签到失败，凭据出错"}
    except:
        traceback.print_exc()
        return {"Error": "签到失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/invalidateToken")
@app.post("/logout")
async def invalidate_token(uid: int, token: str):
    cuid = veriToken.verificationToken(uid, token)
    try:
        if cuid != -1:
            rtn = sql.session.query(sql.tokenList).filter(sql.tokenList.uid == cuid).delete()
            sql.session.commit()
            if rtn == 1:
                return {"Msg": "登出成功"}
            else:
                raise Exception
        return {"Msg": "登出失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"Msg": "登出失败，服务器内部错误" + " 请联系: " + adminMail}


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
        traceback.print_exc()
        return {"Error": "习惯添加失败，服务器内部错误" + " 请联系: " + adminMail}


# 查询好习惯 f'{hname}'为格式化字符串，注意引号
@app.get("/selhabits")
async def sel_habits(hname: str = None, hcategory: str = None):
    try:
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
    except:
        traceback.print_exc()
        return {"Error": "查询习惯失败，服务器内部错误" + " 请联系: " + adminMail}


@app.get("/selmyhabits")
async def sel_my_habits(uid: int, token: str):
    cuid = veriToken.verificationToken(uid, token)
    try:
        if cuid != -1:
            return sql.session.query(sql.goodHabits).filter(sql.goodHabits.cuid == cuid).all()
        return {"Error": "查询自定义习惯失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"Error": "查询自定义习惯失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/modhabit")
async def mod_habit(uid: int, token: str, hid: int, hname: str = None, hcontent: str = None, hcategory: str = None):
    cuid = veriToken.verificationToken(uid, token)
    try:
        if cuid != -1:
            if tuple([hid]) in sql.session.query(sql.goodHabits.hid).filter(sql.goodHabits.cuid == cuid).all():
                if hname is not None:
                    sql.session.query(sql.goodHabits).filter(sql.goodHabits.hid == hid) \
                        .update({sql.goodHabits.hname: hname})
                    sql.session.commit()
                if hcontent is not None:
                    sql.session.query(sql.goodHabits).filter(sql.goodHabits.hid == hid) \
                        .update({sql.goodHabits.hcontent: hcontent})
                    sql.session.commit()
                if hcategory is not None:
                    sql.session.query(sql.goodHabits).filter(sql.goodHabits.hid == hid) \
                        .update({sql.goodHabits.hcategory: hcategory})
                    sql.session.commit()
                return {"Msg": "修改成功"}
            return {"Error": "修改失败，无权操作他人的习惯"}
        return {"Error": "修改失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"Error": "修改失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/delhabit")
async def del_habit(uid: int, token: str, hid: int):
    cuid = veriToken.verificationToken(uid, token)
    try:
        if cuid != -1:
            if tuple([hid]) in sql.session.query(sql.goodHabits.hid).filter(sql.goodHabits.cuid == cuid).all():
                sql.session.query(sql.goodHabits).filter(sql.goodHabits.hid == hid).delete()
                sql.session.commit()
                return {"Msg": "删除成功"}
            return {"Error": "删除失败，无权操作他人的习惯"}
        return {"Error": "删除失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"Error": "删除失败，服务器内部错误" + " 请联系: " + adminMail}


if __name__ == '__main__':
    uvicorn.run(app='main:app', host="127.0.0.1", port=8000, reload=True, debug=True)
