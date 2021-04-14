import datetime
import hashlib
import os
import traceback
from multiprocessing import Pool
from random import random

import uvicorn
from fastapi import FastAPI
from sqlalchemy import func

import utils.creditUtils as credit
import utils.sqlUtils as sql
import utils.veriToken as veriToken
from utils import gen_habit_plaza, habitUtils

app = FastAPI()

# 公用变量
adminMail = "admin@admin.com"


# TODO 使用状态码 code 返回程序执行状态
@app.get("/")
async def read_root():
    return {"这里是": "好习惯养成系统"}


'''
--管理员部分--
'''


# 管理员注册
# 管理员只能有一个
@app.post("/registerForAdmin")
async def register_for_admin(admin_name: str, admin_pwd: str):
    try:
        sql.session.commit()
        isadminexist = sql.session.query(sql.admin.admin_name).first() is not None
        if isadminexist:
            return {"code": -1, "Msg": "管理员已存在，只能存在一个管理员"}
        else:
            # 密码加密处理在客户端
            new_admin = sql.admin(admin_name=admin_name, admin_pwd=admin_pwd)
            sql.session.add(new_admin)
            sql.session.commit()
            return {"code": 0, "Msg": "管理员注册成功"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "管理员注册失败，服务器内部错误" + " 请联系: " + adminMail}


# 管理员登录
@app.post("/loginForAdmin")
async def log_in_for_admin(admin_name: str, admin_pwd: str):
    try:
        sql.session.commit()
        cadmin = sql.session.query(sql.admin).filter(sql.admin.admin_name == admin_name).first()
        # 判空
        if cadmin is None:
            return {"code": -1, "Msg": "管理员登录失败，用户不存在"}
        cpwd = cadmin.admin_pwd
        if admin_pwd == cpwd:  # 验证账号密码
            timenext = datetime.datetime.now() + datetime.timedelta(days=3)
            token = hashlib.sha1(os.urandom(32)).hexdigest()
            sql.session.query(sql.admin).filter(sql.admin.admin_name == admin_name) \
                .update({"admin_token": token, "expire_time": timenext})
            sql.session.commit()
            return {"code": 0, "admin_name": admin_name, "admin_token": token}
        else:
            return {"code": -1, "Msg": "管理员登录失败"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "管理员登录失败，服务器内部错误" + " 请联系: " + adminMail}


# 管理员审核好习惯
@app.post("/reviewHabitAdmin")
async def review_habit_admin(admin_token: str, hid: int, operation: int):
    try:
        sql.session.commit()
        if admin_token != sql.session.query(sql.admin.admin_token).first()[0]:
            return {"code": -1, "Msg": "审核好习惯失败，管理员登录失效"}
        if operation == 1:
            sql.session.query(sql.good_habits).filter(sql.good_habits.hid == hid) \
                .update({sql.good_habits.habit_isvisible: True})
        elif operation == 2:
            sql.session.query(sql.good_habits).filter(sql.good_habits.hid == hid) \
                .delete()
        else:
            return {"code": -1, "Msg": "审核好习惯失败，操作码错误"}
        sql.session.commit()
        return {"code": 0, "Msg": "审核好习惯成功，操作：" + ("通过" if operation == 1 else "删除")}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "审核好习惯失败，服务器内部错误" + " 请联系: " + adminMail}


# 管理员查询好习惯
@app.post("/selHabitsAdmin")
async def sel_habits_admin(admin_token: str, hname: str = None, hcategory: str = None):
    try:
        sql.session.commit()
        if admin_token != sql.session.query(sql.admin.admin_token).first()[0]:
            return {"code": -1, "Msg": "查询习惯失败，管理员登录失效"}
        habits = habitUtils.sel_habits(True, hname, hcategory)
        return {"code": 0, "result": habits}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "查询习惯失败，服务器内部错误" + " 请联系: " + adminMail}


# TODO 用户行为评估得出好习惯分数->用户等级

'''
--用户部分--
'''


# 注册
@app.post("/register")
async def register(uname: str, uprofile: str, upwd: str):
    try:
        sql.session.commit()
        isnameexist = sql.session.query(sql.user.user_name).filter(sql.user.user_name == uname).first() is not None
        if isnameexist:
            return {"code": -1, "Msg": "名称已存在"}
        else:
            # 密码加密处理在客户端
            new_user = sql.user(user_name=uname, user_profile=uprofile, user_pwd=upwd)
            sql.session.add(new_user)
            sql.session.commit()
            return {"code": 0, "Msg": "注册成功"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "注册失败，服务器内部错误" + " 请联系: " + adminMail}


# 登录
@app.post("/login")
async def log_in(uname: str, upwd: str):
    try:
        sql.session.commit()
        cuser = sql.session.query(sql.user).filter(sql.user.user_name == uname).first()
        # 判空
        if cuser is None:
            return {"code": -1, "Msg": "登录失败，用户不存在"}
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
            return {"code": 0, "uid": cuid, "user_name": uname, "user_profile": cuser.user_profile, "user_token": token}
        else:
            return {"code": -1, "Msg": "登录失败"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "登录失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/updateUser")
async def update_user(uid: int, token: str, uprofile: str = None, upwd: str = None):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            if uprofile is not None:
                if len(uprofile) != 0:
                    sql.session.commit()
                    sql.session.query(sql.user).filter(sql.user.uid == uid).update({sql.user.user_profile: uprofile})
                    sql.session.commit()
            if upwd is not None:
                if len(upwd) != 0:
                    sql.session.commit()
                    sql.session.query(sql.user).filter(sql.user.uid == uid).update({sql.user.user_pwd: upwd})
                    sql.session.commit()
            return {"code": 0, "Msg": "用户信息修改成功"}
        return {"code": -1, "Msg": "用户信息修改失败，凭据无效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "用户信息修改失败，服务器内部错误" + " 请联系: " + adminMail}


# TODO 达到积分完成习惯
# 签到
@app.post("/qiandao")
async def clock_in(uid: int, token: str):
    global lqcount
    try:
        cuid = veriToken.verification_token(uid, token)
        if cuid != -1:
            sql.session.commit()  # 清除查询缓存
            if sql.session.query(sql.clock_in).filter(
                    sql.clock_in.uid == cuid,
                    func.to_days(sql.clock_in.last_qd_time) == func.to_days(func.now())).first() is not None:
                return {"code": -1, "Msg": "签到失败，你今天已经签到过了"}
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
            if credit.credit_add(cuid, 10 * lqcount, "每日签到") == 0:  # 连签积分加成
                sql.session.commit()
                return {"code": 0, "Msg": "签到成功，积分+" + str(10 * lqcount)}
            else:
                raise Exception
        return {"code": -1, "Msg": "签到失败，凭据出错"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "签到失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/chkToken")
async def chk_token(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    if cuid == uid:
        return {"code": 0, "Msg": "Token有效"}
    else:
        return {"code": -1, "Msg": "Token无效"}


@app.post("/invalidateToken")
@app.post("/logout")
async def invalidate_token(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            rtn = sql.session.query(sql.token_list).filter(sql.token_list.uid == cuid).delete()
            sql.session.commit()
            if rtn == 1:
                return {"code": 0, "Msg": "登出成功"}
            else:
                raise Exception
        return {"code": -1, "Msg": "登出失败，凭据失效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "登出失败，服务器内部错误" + " 请联系: " + adminMail}


'''
--积分部分--
'''


# 获取积分总数目
@app.post("/getCredit")
async def get_credit(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            return {"code": 0, "Uid": cuid, "CreditSum": credit.get_credit(cuid)[0]}
        else:
            return {"code": -1, "Msg": "查询积分失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "查询积分失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/creditDetail")
async def credit_detail(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            result = credit.get_credit_detail(cuid)
            if result is None:
                return {"code": -1, "Msg": "积分详情异常"}
            return {"code": 0, "result": result}
        else:
            return {"code": -1, "Msg": "查询积分详情失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "查询积分详情失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/creditLottery")
async def credit_lottery(uid: int, token: str, count: int = 10):
    if count <= 0 or count > 20:
        return {"code": -1, "Msg": "积分抽奖失败，次数无效，请检查"}
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            result = credit.credit_lottery_duo(cuid, count)
            if len(result) == 0:
                return {"code": -1, "Msg": "积分抽奖失败，积分不足"}
            return {"code": 0, "Uid": cuid, "Index": result}
        else:
            return {"code": -1, "Msg": "积分抽奖失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "积分抽奖失败，服务器内部错误" + " 请联系: " + adminMail}


'''
--习惯部分--
'''


# 添加好习惯
@app.post("/addhabit")
async def add_habit(uid: int, token: str, hname: str, hcontent: str, hcategory: str = None):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            if len(hcategory) == 0:
                hcategory = "其他"
            new_habit = sql.good_habits(create_uid=cuid, habit_name=hname, habit_content=hcontent,
                                        habit_category=hcategory, habit_create_time=datetime.datetime.now())
            sql.session.add(new_habit)
            sql.session.commit()
            return {"code": 0, "Msg": "习惯添加成功"}
        else:
            return {"code": -1, "Msg": "习惯添加失败，凭据失效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "习惯添加失败，服务器内部错误" + " 请联系: " + adminMail}


@app.get("/selhabits")
async def sel_habits(hname: str = None, hcategory: str = None):
    try:
        habits = habitUtils.sel_habits(False, hname, hcategory)
        return {"code": 0, "result": habits}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "查询习惯失败，服务器内部错误" + " 请联系: " + adminMail}


@app.get("/selmyhabits")
async def sel_my_habits(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            return {"code": 0, "result": sql.session.query(sql.good_habits).filter(
                sql.good_habits.create_uid == cuid).all()}
        return {"code": -1, "Msg": "查询自定义习惯失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "查询自定义习惯失败，服务器内部错误" + " 请联系: " + adminMail}


# TODO 修改完更改可视性为否
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
                return {"code": 0, "Msg": "修改成功"}
            return {"code": -1, "Msg": "修改失败，无权操作他人的习惯"}
        return {"code": -1, "Msg": "修改失败，凭据失效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "修改失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/delhabit")
async def del_habit(uid: int, token: str, hid: int):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            if tuple([hid]) in sql.session.query(sql.good_habits.hid).filter(sql.good_habits.create_uid == cuid).all():
                sql.session.query(sql.good_habits).filter(sql.good_habits.hid == hid).delete()
                sql.session.commit()
                return {"code": 0, "Msg": "删除成功"}
            return {"code": -1, "Msg": "删除失败，无权操作他人的习惯"}
        return {"code": -1, "Msg": "删除失败，凭据失效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "删除失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/buyhabit")
async def buy_habit(uid: int, token: str, hid: int, user_config: str, target_days: int, capital: int):
    cuid = veriToken.verification_token(uid, token)
    multiple = credit.cal_multiple(target_days, capital)
    bonus = capital * multiple
    try:
        if cuid != -1:
            habit_to_buy = sql.session.query(sql.good_habits).filter(sql.good_habits.hid == hid).first()
            ret = credit.credit_consume(uid, capital, "购买习惯：" + habit_to_buy.habit_name)
            if ret == -1:
                return {"code": -1, "Msg": "购买习惯失败，积分余额不足"}
            rh = sql.running_habits(hid=hid, uid=uid, user_config=user_config,
                                    bonus=bonus, target_days=target_days,
                                    running_start_time=datetime.datetime.now())
            sql.session.query(sql.good_habits).filter(sql.good_habits.hid == hid).update(
                {sql.good_habits.habit_heat: sql.good_habits.habit_heat + 1})
            sql.session.add(rh)
            sql.session.commit()
            return {"code": 0, "Msg": "购买习惯成功，返还积分 " + str(bonus)}
        return {"code": -1, "Msg": "购买习惯失败，用户不存在"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "购买习惯失败，服务器内部错误" + " 请联系: " + adminMail}


# TODO 习惯签到返还积分
@app.post("/habitclockin")
async def habit_clock_in(uid: int, token: str, rhid: int):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            sql.session.commit()
            habit_to_clock_in = sql.session.query(sql.running_habits).filter(sql.running_habits.rhid == rhid).first()
            # 检查是否为本人习惯 sql=1
            if habit_to_clock_in.uid != cuid:
                return {"code": -1, "Msg": "习惯打卡失败，不可以为他人习惯打卡"}
            # 检查是否达标 sql=1
            if habit_to_clock_in.persist_days == habit_to_clock_in.target_days:
                return {"code": -1, "Msg": "习惯打卡失败，已打卡到目标天数"}
            # 检查是否已打卡过 sql=2
            if sql.session.query(sql.running_habits).filter(
                    sql.running_habits.rhid == rhid,
                    func.to_days(sql.running_habits.last_qd_time) == func.to_days(func.now())).first() is not None:
                return {"code": -1, "Msg": "习惯打卡失败，你今天已经打卡过了"}
            # 最后一天打卡 sql=3
            if habit_to_clock_in.persist_days + 1 == habit_to_clock_in.target_days:
                temp_bonus = habit_to_clock_in.bonus
                sql.session.query(sql.running_habits).filter(sql.running_habits.rhid == rhid).update(
                    {sql.running_habits.persist_days: sql.running_habits.persist_days + 1,
                     sql.running_habits.last_qd_time: datetime.datetime.now(),
                     sql.running_habits.bonus: 0})  # 此处操作对habit_to_clock_in生效
                credit.credit_add(cuid, temp_bonus, "习惯打卡返还")
                sql.session.commit()
                return {"code": 0,
                        "Msg": "习惯打卡成功，当前打卡第" + str(habit_to_clock_in.persist_days) +
                               "天，返还积分" + str(temp_bonus)}
            # 正常打卡 sql=3
            bonus = int(habit_to_clock_in.bonus / (habit_to_clock_in.target_days - habit_to_clock_in.persist_days)
                        - int(random() * 10))
            bonus = 1 if bonus == 0 else bonus  # 判断返还积分是否为0
            sql.session.query(sql.running_habits).filter(sql.running_habits.rhid == rhid).update(
                {sql.running_habits.persist_days: sql.running_habits.persist_days + 1,
                 sql.running_habits.last_qd_time: datetime.datetime.now(),
                 sql.running_habits.bonus: sql.running_habits.bonus - bonus})  # 此处操作对habit_to_clock_in生效
            credit.credit_add(cuid, bonus, "习惯打卡返还")
            sql.session.commit()
            return {"code": 0,
                    "Msg": "习惯打卡成功，当前打卡第" + str(habit_to_clock_in.persist_days) + "天，返还积分" + str(bonus)}
        return {"code": -1, "Msg": "习惯打卡失败，输入信息有误"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "习惯打卡失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/giveuphabit")
async def give_up_habit(uid: int, token: str, rhid: int):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            ret = sql.session.query(sql.running_habits).filter(
                sql.running_habits.uid == uid, sql.running_habits.rhid == rhid).delete()
            sql.session.commit()
            if ret != 0:
                return {"code": 0, "Msg": "放弃习惯成功"}
            else:
                return {"code": -1, "Msg": "放弃习惯失败，输入信息有误"}
        return {"code": -1, "Msg": "放弃习惯失败，用户不存在"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "放弃习惯失败，服务器内部错误" + " 请联系: " + adminMail}


# TODO 好习惯广场 top10习惯
@app.get("/habitplaza")
async def habit_plaza():
    try:
        sql.session.commit()
        top10 = sql.session.query(sql.habit_plaza).all()
        return {"code": 0, "result": top10}
    except:
        return {"code": -1, "Msg": "查询习惯广场失败，服务器内部错误" + " 请联系: " + adminMail}


if __name__ == '__main__':
    pool = Pool(processes=1)
    pool.apply_async(gen_habit_plaza.gen, args=(10, False))
    print("主进程 [%s]" % os.getpid())
    uvicorn.run(app='main:app', host="0.0.0.0", port=8000, reload=True, debug=True)
    pool.close()
    pool.join()
