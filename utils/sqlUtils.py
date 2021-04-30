# sqlalchemy配置
import datetime

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URI: str = 'mysql+pymysql://habitsys_final:FTk8BPzitCXPkGc7@goodhabitsys.moecola.com:3306' \
                               '/habitsys_final'
# 生成一个SQLAlchemy引擎
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)

# 生成sessionlocal类，这个类的每一个实例都是一个数据库的会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()
Base = declarative_base()


# 管理员表
class admin(Base):
    __tablename__ = "admin"
    admin_name = Column(String(100), primary_key=True)
    admin_pwd = Column(String(64))
    admin_token = Column(String(40))
    expire_time = Column(DateTime)


# 用户表
class user(Base):
    __tablename__ = "user"
    uid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(100))
    user_profile = Column(String(500))
    user_pwd = Column(String(64))
    user_score = Column(Integer, default=1000)
    credit_sum = Column(Integer, default=0)
    lottery_sum = Column(Integer, default=0)  # 小保底计数
    lottery_Ssum = Column(Integer, default=0)  # 大保底计数
    last_qd_time = Column(DateTime, default=datetime.datetime(1970, 1, 1, 0, 0))  # 最后签到时间
    lq_count = Column(Integer, default=0)  # 连签天数
    token = Column(String(40), default="")
    expire_time = Column(DateTime, default=datetime.datetime(1970, 1, 1, 0, 0))


# 好习惯模板表
class good_habits(Base):
    __tablename__ = "good_habits"
    hid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    create_uid = Column(Integer, ForeignKey(user.uid))
    habit_name = Column(String(500))
    habit_content = Column(String(5000))
    habit_category = Column(String(500), default="其他")
    habit_heat = Column(Integer, default=0)
    habit_create_time = Column(DateTime)
    habit_isvisible = Column(Boolean, default=True)  # 测试时默认可视


# 进行中的好习惯
class running_habits(Base):
    __tablename__ = "running_habits"
    rhid = Column(Integer, primary_key=True, autoincrement=True)
    hid = Column(Integer, ForeignKey(good_habits.hid))
    uid = Column(Integer, ForeignKey(user.uid), index=True)
    user_config = Column(String(5000))
    bonus = Column(Integer)
    persist_days = Column(Integer, default=0)
    target_days = Column(Integer)
    last_qd_time = Column(DateTime, default=datetime.datetime(1970, 1, 1, 0, 0))
    running_start_time = Column(DateTime)


# 习惯广场表
class habit_plaza(Base):
    __tablename__ = "habit_plaza"
    hid = Column(Integer, primary_key=True, index=True)
    create_uid = Column(Integer)
    habit_name = Column(String(500))
    habit_content = Column(String(5000))
    habit_category = Column(String(500))
    habit_heat = Column(Integer)
    habit_create_time = Column(DateTime)
    habit_isvisible = Column(Boolean, default=True)


# 积分记录表
class credit_detail(Base):
    __tablename__ = "credit_detail"
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(Integer, ForeignKey(user.uid), index=True)
    credit_num = Column(Integer)  # 积分数额
    credit_desc = Column(String(500))  # 积分描述
    credit_time = Column(DateTime)  # 记录时间


# 商品兑换表
class exchange_goods(Base):
    __tablename__ = "exchange_goods"
    gid = Column(Integer, primary_key=True, autoincrement=True)
    goods_name = Column(String(500))
    goods_pic_b64 = Column(String(600000))
    goods_price = Column(Integer, default=9999)
    goods_stock = Column(Integer, default=1)


Base.metadata.create_all(bind=engine)
