import utils.sqlUtils as sql
import datetime


def creditAdd(uid: int, creditnum: int):
    ret = sql.session.query(sql.credit).filter(sql.credit.uid == uid) \
        .update({sql.credit.creditsum: sql.credit.creditsum + creditnum}, synchronize_session=False)
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
