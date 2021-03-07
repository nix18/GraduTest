import time
from threading import Thread

import uvicorn
from fastapi import FastAPI
import datetime

from sqlalchemy import func

import utils.sqlUtils as sql
import utils.creditUtils as credit
import utils.veriToken as veriToken
import hashlib
import traceback
import os

app = FastAPI()

# 公用变量
adminMail = "admin@admin.com"


# TODO 使用状态码 code 返回程序执行状态
@app.get("/")
async def read_root():
    return {"Hello": "Test"}


# 查询
@app.get("/query")
async def query(uid: int, token: str):
    if veriToken.verification_token(uid, token) != -1:
        pass
    else:
        return {"Error": "登陆错误，凭据失效"}
    qd_list = []
    qd = sql.session.query(sql.clock_in).all()
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
        isnameexist = sql.session.query(sql.user.user_name).filter(sql.user.user_name == uname).first() is not None
        if isnameexist:
            return {"Error": "名称已存在"}
        else:
            # 密码加密处理在客户端
            new_user = sql.user(user_name=uname, user_profile=uprofile, user_pwd=upwd)
            sql.session.add(new_user)
            sql.session.commit()
            return {"Msg": "注册成功"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"Error": "注册失败，服务器内部错误" + " 请联系: " + adminMail}


# 登录
@app.post("/login")
async def log_in(uname: str, upwd: str):
    try:
        cuser = sql.session.query(sql.user).filter(sql.user.user_name == uname).first()
        # 判空
        if cuser is None:
            return {"Error": "登录失败"}
        cpwd = cuser.user_pwd
        cuid = cuser.uid
        if upwd == cpwd:  # 验证账号密码
            isexist = sql.session.query(sql.token_list.token).filter(sql.token_list.uid == cuid).first()
            timenext = datetime.datetime.now() + datetime.timedelta(days=3)
            token = hashlib.sha1(os.urandom(32)).hexdigest()
            if isexist is None:
                new_token = sql.token_list(uid=cuid, token=token,
                                           expire_time=timenext)
                sql.session.add(new_token)
            else:
                sql.session.query(sql.token_list).filter(sql.token_list.uid == cuid) \
                    .update({"token": token, "expire_time": timenext})
            sql.session.commit()
            return {"Uid": cuid, "Token": token}
        else:
            return {"Error": "登录失败"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"Error": "登录失败，服务器内部错误" + " 请联系: " + adminMail}


# TODO 达到积分完成习惯
# 签到
@app.post("/qiandao")
async def clock_in(uname: str, token: str):
    global lqcount
    try:
        cuid = veriToken.verification_token(uname, token)
        if cuid != -1:
            sql.session.commit()  # 清除查询缓存
            if sql.session.query(sql.clock_in).filter(
                    sql.clock_in.uid == cuid,
                    func.to_days(sql.clock_in.last_qd_time) == func.to_days(func.now())).first() is not None:
                return {"Error": "签到失败，你今天已经签到过了"}
            lqobj = sql.session.query(sql.clock_in).filter(sql.clock_in.uid == cuid).first()
            if lqobj is None:
                lqcount = 1
                new_qd = sql.clock_in(uid=cuid, last_qd_time=datetime.datetime.now(), lq_count=1)
                sql.session.add(new_qd)
            else:
                lqdate = lqobj.last_qd_time
                lqcount = lqobj.lq_count
                if lqdate.date() == datetime.datetime.now().date() - datetime.timedelta(days=1):
                    lqcount = (lqcount + 1) % 8
                    if lqcount == 0:
                        lqcount = 1
                else:
                    lqcount = 1
                sql.session.query(sql.clock_in).filter(sql.clock_in.uid == cuid).update(
                    {sql.clock_in.last_qd_time: datetime.datetime.now(), sql.clock_in.lq_count: lqcount})
            if credit.credit_add(cuid, 10 * lqcount, "每日签到") == 1:  # 连签积分加成
                sql.session.commit()
                return {"Msg": "签到成功，积分+" + str(10 * lqcount)}
            else:
                raise Exception
        return {"Error": "签到失败，凭据出错"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"Error": "签到失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/invalidateToken")
@app.post("/logout")
async def invalidate_token(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            rtn = sql.session.query(sql.token_list).filter(sql.token_list.uid == cuid).delete()
            sql.session.commit()
            if rtn == 1:
                return {"Msg": "登出成功"}
            else:
                raise Exception
        return {"Msg": "登出失败，凭据失效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"Msg": "登出失败，服务器内部错误" + " 请联系: " + adminMail}


# 获取积分总数目
@app.post("/getCredit")
async def get_credit(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            return {"Uid": cuid, "CreditSum": credit.get_credit(cuid)[0]}
        else:
            return {"Error": "查询积分失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"Error": "查询积分失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/creditLottery")
async def credit_lottery(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            result = credit.credit_lottery_duo(cuid, 10)
            if len(result) == 0:
                return {"Error": "积分抽奖失败，积分不足"}
            return {"Uid": cuid, "Index": result}
        else:
            return {"Error": "积分抽奖失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"Error": "积分抽奖失败，服务器内部错误" + " 请联系: " + adminMail}


# 添加好习惯
@app.post("/addhabit")
async def add_habit(uid: int, token: str, hname: str, hcontent: str, hcategory: str = None):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            new_habit = sql.good_habits(create_uid=cuid, habit_name=hname, habit_content=hcontent,
                                        habit_category=hcategory, habit_create_time=datetime.datetime.now())
            sql.session.add(new_habit)
            sql.session.commit()
            return {"Msg": "习惯添加成功"}
        else:
            return {"Error": "习惯添加失败，凭据失效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"Error": "习惯添加失败，服务器内部错误" + " 请联系: " + adminMail}


# 查询好习惯 f'{hname}'为格式化字符串，注意引号
@app.get("/selhabits")
async def sel_habits(hname: str = None, hcategory: str = None):
    try:
        if hname is None:
            if hcategory is None:
                habits = sql.session.query(sql.good_habits).all()
            else:
                habits = sql.session.query(sql.good_habits).filter(
                    sql.good_habits.habit_category.like(f'%{hcategory}%')).all()
        else:
            if hcategory is None:
                habits = sql.session.query(sql.good_habits).filter(sql.good_habits.habit_name.like(f'%{hname}%')).all()
            else:
                habits = sql.session.query(sql.good_habits).filter(
                    sql.good_habits.habit_name.like(f'%{hname}%'),
                    sql.good_habits.habit_category.like(f'%{hcategory}%')).all()
        return habits
    except:
        traceback.print_exc()
        return {"Error": "查询习惯失败，服务器内部错误" + " 请联系: " + adminMail}


@app.get("/selmyhabits")
async def sel_my_habits(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            return sql.session.query(sql.good_habits).filter(sql.good_habits.create_uid == cuid).all()
        return {"Error": "查询自定义习惯失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"Error": "查询自定义习惯失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/modhabit")
async def mod_habit(uid: int, token: str, hid: int, hname: str = None, hcontent: str = None, hcategory: str = None):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            if tuple([hid]) in sql.session.query(sql.good_habits.hid).filter(sql.good_habits.create_uid == cuid).all():
                if hname is not None:
                    sql.session.query(sql.good_habits).filter(sql.good_habits.hid == hid) \
                        .update({sql.good_habits.habit_name: hname})
                    sql.session.commit()
                if hcontent is not None:
                    sql.session.query(sql.good_habits).filter(sql.good_habits.hid == hid) \
                        .update({sql.good_habits.habit_content: hcontent})
                    sql.session.commit()
                if hcategory is not None:
                    sql.session.query(sql.good_habits).filter(sql.good_habits.hid == hid) \
                        .update({sql.good_habits.habit_category: hcategory})
                    sql.session.commit()
                return {"Msg": "修改成功"}
            return {"Error": "修改失败，无权操作他人的习惯"}
        return {"Error": "修改失败，凭据失效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"Error": "修改失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/delhabit")
async def del_habit(uid: int, token: str, hid: int):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            if tuple([hid]) in sql.session.query(sql.good_habits.hid).filter(sql.good_habits.create_uid == cuid).all():
                sql.session.query(sql.good_habits).filter(sql.good_habits.hid == hid).delete()
                sql.session.commit()
                return {"Msg": "删除成功"}
            return {"Error": "删除失败，无权操作他人的习惯"}
        return {"Error": "删除失败，凭据失效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"Error": "删除失败，服务器内部错误" + " 请联系: " + adminMail}


# TODO 好习惯top10生成 根据热度habit_heat每小时1次更新
class gen_habit_plaza(Thread):
    def __init__(self):
        super().__init__()
        print("习惯广场线程已初始化")

    def run(self):
        while True:
            print("已更新习惯广场 " + str(datetime.datetime.now()))
            time.sleep(10)


# TODO 好习惯广场 top10习惯+自己的习惯
@app.get("/habitplaza")
async def habit_plaza():
    return


if __name__ == '__main__':
    gen_habit_plaza().start()  # 启动更新习惯广场线程
    uvicorn.run(app='main:app', host="127.0.0.1", port=8000, reload=True, debug=True)
