import datetime
import hashlib
import os
import traceback
from multiprocessing import Pool
from random import random

import requests
import uvicorn
from fastapi import FastAPI
from sqlalchemy import func, DATE, cast

import utils.creditUtils as credit
import utils.sqlUtils as sql
import utils.veriToken as veriToken
from utils import habitUtils
from workers import weixinRemindWorker, genHabitPlazaWorker, genUserScoreWorker

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
            user = sql.session.query(sql.user).filter(sql.user.user_name == uname).first()
            credit.credit_add(user.uid, 0, "积分账户初始化")
            credit.credit_add(user.uid, 500, "注册赠送500积分")
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


@app.post("/login_WX")
async def login_WX(uname: str, upwd: str):
    try:
        uname = "WX_" + uname[-12:-1]
        sql.session.commit()
        isnameexist = sql.session.query(sql.user.user_name).filter(sql.user.user_name == uname).first() is not None
        if isnameexist:
            pass
        else:
            # 密码加密处理在客户端
            new_user = sql.user(user_name=uname, user_profile="", user_pwd=upwd)
            sql.session.add(new_user)
            sql.session.commit()
        # 登录
        cuser = sql.session.query(sql.user).filter(sql.user.user_name == uname).first()
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
            return {"code": 0, "uid": cuid, "user_profile": cuser.user_profile, "user_token": token}
        else:
            return {"code": -1, "Msg": "登录失败"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "用户注册失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/getInfoWX")
async def get_Info_WX(code: str):
    url = "https://api.weixin.qq.com/sns/jscode2session"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/70.0.3538.77 Safari/537.36 '
    }
    r = requests.get(url,
                     params={'appid': 'wxf7d1deaed7693c86', 'secret': '2d514ef6be29f82454f95588dbbab7eb',
                             'js_code': code, 'grant_type': 'authorization_code'}, headers=headers, verify=False)
    return r.json()


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
async def chk_token(uid: int, token: str, iswx: int = None):
    cuid = veriToken.verification_token(uid, token)
    if cuid == uid:
        if iswx == 1:
            return {"code": 0, "user_profile":
                sql.session.query(sql.user.user_profile).filter(sql.user.uid == uid).first()[0], "Msg": "Token有效"}
        return {"code": 0, "Msg": "Token有效"}
    else:
        return {"code": -1, "Msg": "Token无效"}


@app.post("/getUserScore")
async def get_user_score(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            ret = sql.session.query(sql.user.user_score).filter(sql.user.uid == cuid).first()[0]
            return {"code": 0, "uid": cuid, "score": ret}
        return {"code": -1, "Msg": "查询用户score失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "查询用户score失败，服务器内部错误" + " 请联系: " + adminMail}


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


@app.get("/getExchangeGoods")
async def get_exchange_goods():
    try:
        sql.session.commit()
        ret = sql.session.query(sql.exchange_goods).all()
        return {"code": 0, "result": ret}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "查询商品列表失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/exchangeGoods")
async def exchange_goods(uid: int, token: str, gid: int):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            sql.session.commit()
            sel_goods = sql.session.query(sql.exchange_goods).filter(sql.exchange_goods.gid == gid).first()
            if sel_goods.goods_stock <= 0:
                return {"code": -1, "Msg": "积分兑换失败，库存不足"}
            ret = credit.credit_consume(cuid, sel_goods.goods_price, "积分兑换：" + sel_goods.goods_name)
            if ret == -1:
                return {"code": -1, "Msg": "积分兑换失败，积分不足"}
            sql.session.query(sql.exchange_goods).filter(sql.exchange_goods.gid == gid).update(
                {sql.exchange_goods.goods_stock: sql.exchange_goods.goods_stock - 1}
            )
            sql.session.commit()
            return {"code": 0, "Msg": "积分兑换成功，商品:" + sel_goods.goods_name + "，请联系客服提供邮递方式后领取"}
        return {"code": -1, "Msg": "积分兑换失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "积分兑换失败，服务器内部错误" + " 请联系: " + adminMail}


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


@app.post("/getCreditAnalyse")
async def get_credit_analyse(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            time_limit = datetime.datetime.today() + datetime.timedelta(days=-30)
            data_list = [0, 0, 0, 0, 0]
            sql.session.commit()
            records = sql.session.query(sql.credit_detail). \
                filter(sql.credit_detail.uid == uid,
                       cast(sql.credit_detail.credit_time, DATE) >= time_limit).all()
            for record in records:
                if "签到" in record.credit_desc:
                    data_list[0] += record.credit_num
                if "习惯打卡" in record.credit_desc:
                    data_list[1] += record.credit_num
                if "购买" in record.credit_desc:
                    data_list[2] += record.credit_num
                if "兑换" in record.credit_desc:
                    data_list[3] += record.credit_num
                if "抽奖" in record.credit_desc:
                    data_list[4] += record.credit_num
            return {"code": 0, "data1": data_list[0], "data2": data_list[1], "data3": data_list[2],
                    "data4": data_list[3], "data5": data_list[4]}
        return {"code": -1, "Msg": "查询积分分析失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "查询积分分析失败，服务器内部错误" + " 请联系: " + adminMail}


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


@app.post("/selHabitByHid")
async def sel_habit_by_hid(uid: int, token: str, hid: int):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            sql.session.commit()
            return {"code": 0, "result": habitUtils.sel_habit_by_hid(hid)}
        return {"code": -1, "Msg": "通过Hid查询习惯失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "通过Hid查询习惯失败，服务器内部错误" + " 请联系: " + adminMail}


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
        return {"code": -1, "Msg": "删除失败，可能有用户正在养成此习惯，如果仍想删除" + " 请联系: " + adminMail}


@app.post("/buyhabit")
async def buy_habit(uid: int, token: str, hid: int, user_config: str, target_days: int, capital: int):
    cuid = veriToken.verification_token(uid, token)
    multiple = credit.cal_multiple(target_days, capital)
    bonus = capital * multiple
    try:
        if cuid != -1:
            sql.session.commit()
            if sql.session.query(sql.running_habits).filter(sql.running_habits.uid == cuid).count() >= 20:
                return {"code": -1, "Msg": "购买习惯失败，达到养成中习惯最大值20"}
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
        return {"code": -1, "Msg": "购买习惯失败，凭据失效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "购买习惯失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/updateRunningHabit")
async def update_running_habit(uid: int, token: str, rhid: int, user_config: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            sql.session.commit()
            if sql.session.query(sql.running_habits.uid).filter(sql.running_habits.rhid == rhid).first()[0] == uid:
                sql.session.query(sql.running_habits).filter(sql.running_habits.rhid == rhid).update(
                    {sql.running_habits.user_config: user_config})
                sql.session.commit()
                return {"code": 0, "Msg": "更新养成中习惯成功"}
            return {"code": -1, "Msg": "更新养成中习惯失败，不可以修改他人习惯"}
        return {"code": -1, "Msg": "更新养成中习惯失败，凭据失效"}
    except:
        traceback.print_exc()
        sql.session.rollback()
        return {"code": -1, "Msg": "更新养成中习惯失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/selMyRunningHabits")
async def sel_my_running_habits(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            sql.session.commit()
            running_habits = sql.session.query(sql.running_habits).filter(sql.running_habits.uid == cuid).all()
            return {"code": 0, "result": running_habits}
        return {"code": -1, "Msg": "查询正在养成的习惯失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "查询正在养成的习惯失败，服务器内部错误" + " 请联系: " + adminMail}


# 习惯签到
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


@app.post("/getHabitClockInAnalyse")
async def get_habit_clock_in_analyse(uid: int, token: str):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            data = {}
            now = datetime.datetime.today()
            time_limit = datetime.datetime.today() + datetime.timedelta(days=-30)
            sql.session.commit()
            records = sql.session.query(sql.credit_detail). \
                filter(sql.credit_detail.uid == uid,
                       cast(sql.credit_detail.credit_time, DATE) >= time_limit).order_by(
                sql.credit_detail.id.desc()
            ).all()
            for i in range(30):
                data[now.strftime('%m/%d')] = 0
                for record in records:
                    if "习惯打卡" in record.credit_desc:
                        if record.credit_time.date() == now.date():
                            data[now.strftime('%m/%d')] += 1
                    if record.credit_time.date() < now.date():
                        break
                now += datetime.timedelta(days=-1)
            return {"code": 0, "result": data}
        return {"code": -1, "Msg": "习惯打卡分析失败，凭据失效"}
    except:
        traceback.print_exc()
        return {"code": -1, "Msg": "习惯打卡分析失败，服务器内部错误" + " 请联系: " + adminMail}


@app.post("/giveuphabit")
async def give_up_habit(uid: int, token: str, rhid: int):
    cuid = veriToken.verification_token(uid, token)
    try:
        if cuid != -1:
            ret = sql.session.query(sql.running_habits).filter(
                sql.running_habits.uid == uid, sql.running_habits.rhid == rhid).delete()
            sql.session.commit()
            if ret != 0:
                credit.credit_add(cuid, 0, "放弃好习惯")
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
        top10 = sql.session.query(sql.habit_plaza).order_by(sql.habit_plaza.habit_heat.desc()).all()
        return {"code": 0, "result": top10}
    except:
        return {"code": -1, "Msg": "查询习惯广场失败，服务器内部错误" + " 请联系: " + adminMail}


if __name__ == '__main__':
    pool = Pool(processes=3)
    pool.apply_async(genHabitPlazaWorker.gen, args=(10, False))
    pool.apply_async(weixinRemindWorker.worker, args=(180, False))
    pool.apply_async(genUserScoreWorker.gen, args=("23:30", True))
    print("主进程 [%s]" % os.getpid())
    uvicorn.run(app='main:app', host="0.0.0.0", port=8000, reload=True, debug=True,
                ssl_keyfile="./goodhabitsys.key", ssl_certfile="./goodhabitsys.pem")
    pool.close()
    pool.join()
