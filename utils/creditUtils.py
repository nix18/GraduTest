import utils.sqlUtils as sql
import datetime


def creditAdd(uid: int, creditnum: int, creditdesc: str):
    ret = sql.session.query(sql.credit).filter(sql.credit.uid == uid) \
        .update({sql.credit.creditsum: sql.credit.creditsum + creditnum}, synchronize_session=False)
    creditDetail(uid, creditnum, creditdesc, datetime.datetime.now())
    sql.session.commit()
    if ret == 1:
        return 1
    else:
        isexist = sql.session.query(sql.credit).filter(sql.credit.uid == uid).first()
        if isexist is None:
            new_credit = sql.credit(uid=uid, creditsum=creditnum)
            sql.session.add(new_credit)
            sql.session.commit()
            return 1
        return 0


# TODO
# 积分记录
def creditDetail(uid: int, creditnum: int, creditdesc: str, ctime: datetime.datetime):
    new_creditdetail = sql.creditdetail(
        uid=uid, creditnum=creditnum, creditdesc=creditdesc, ctime=ctime)
    sql.session.add(new_creditdetail)
    sql.session.commit()
    return 1
