import utils.sqlUtils as sql


# 查询好习惯 f'{hname}'为格式化字符串，注意引号
# filter语句内不可以使用is
def sel_habits(isadmin: bool, hname: str = None, hcategory: str = None):
    sql.session.commit()
    if hname is None:
        if hcategory is None:
            # 条件前半句相当于空语句
            habits = sql.session.query(sql.good_habits).filter(
                sql.good_habits.habit_isvisible.like("%") if isadmin else sql.good_habits.habit_isvisible == True).all()
        else:
            habits = sql.session.query(sql.good_habits).filter(
                sql.good_habits.habit_isvisible.like("%") if isadmin else sql.good_habits.habit_isvisible == True,
                sql.good_habits.habit_category.like(
                    f'%{hcategory}%')).all()
    else:
        if hcategory is None:
            habits = sql.session.query(sql.good_habits).filter(
                sql.good_habits.habit_isvisible.like("%") if isadmin else sql.good_habits.habit_isvisible == True,
                sql.good_habits.habit_name.like(f'%{hname}%')).all()
        else:
            habits = sql.session.query(sql.good_habits).filter(
                sql.good_habits.habit_isvisible.like("%") if isadmin else sql.good_habits.habit_isvisible == True,
                sql.good_habits.habit_name.like(f'%{hname}%'),
                sql.good_habits.habit_category.like(
                    f'%{hcategory}%')).all()
    return habits


def sel_habit_by_hid(hid: int):
    if hid > 0:
        return sql.session.query(sql.good_habits).filter(sql.good_habits.hid == hid).first()
    return
