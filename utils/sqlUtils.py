# sqlalchemy配置
import datetime

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URI: str = 'mysql+pymysql://root:locked1234@localhost:3306/goodhabitsys'
# 生成一个SQLAlchemy引擎
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
# 生成sessionlocal类，这个类的每一个实例都是一个数据库的会话
# 注意命名为SessionLocal，与sqlalchemy的session分隔开
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()
Base = declarative_base()


# 用户表
class user(Base):
    __tablename__ = "user"
    uid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(100))
    user_profile = Column(String(500))
    user_pwd = Column(String(64))


# 用户签到表
class clock_in(Base):
    __tablename__ = "clock_in"
    uid = Column(Integer, ForeignKey(user.uid), primary_key=True, index=True)
    last_qd_time = Column(DateTime)  # 最后签到时间
    lq_count = Column(Integer)  # 连签天数


# 用户Token存储表
class token_list(Base):
    __tablename__ = "token_list"
    uid = Column(Integer, ForeignKey(user.uid), primary_key=True, index=True)
    token = Column(String(40))
    expire_time = Column(DateTime)


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


# 积分表
class credit(Base):
    __tablename__ = "credit"
    uid = Column(Integer, ForeignKey(user.uid), primary_key=True, index=True)
    credit_sum = Column(Integer)
    lottery_sum = Column(Integer, default=0)  # 小保底计数
    lottery_Ssum = Column(Integer, default=0)  # 大保底计数


# 积分记录表
class credit_detail(Base):
    __tablename__ = "credit_detail"
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(Integer, ForeignKey(user.uid), index=True)
    credit_num = Column(Integer)  # 积分数额
    credit_desc = Column(String(500))  # 积分描述
    credit_time = Column(DateTime)  # 记录时间


Base.metadata.create_all(bind=engine)
