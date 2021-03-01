# sqlalchemy配置
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URI: str = 'mysql+pymysql://root:locked1234@localhost:3306/testcms'
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
    uname = Column(String(100))
    uprofile = Column(String(500))
    upwd = Column(String(64))


# 用户签到表
class qiandao(Base):
    __tablename__ = "qiandao"
    uid = Column(Integer, primary_key=True, index=True)
    last_qd_time = Column(DateTime)  # 最后签到时间
    lq_count = Column(Integer)  # 连签天数


# 用户Token存储表
class tokenList(Base):
    __tablename__ = "tokenList"
    uid = Column(Integer, primary_key=True, index=True)
    token = Column(String(40))
    expire_time = Column(DateTime)


# 好习惯模板表
class goodHabits(Base):
    __tablename__ = "goodHabits"
    hid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cuid = Column(Integer)
    hname = Column(String(500))
    hcontent = Column(String(5000))
    hcategory = Column(String(500), default="其他")
    htime = Column(DateTime)


# 积分表
class credit(Base):
    __tablename__ = "credit"
    uid = Column(Integer, primary_key=True, index=True)
    creditsum = Column(Integer)
    lotterysum = Column(Integer, default=0)  # 小保底计数
    lotterySsum = Column(Integer, default=0)  # 大保底计数


# 积分记录表
class creditdetail(Base):
    __tablename__ = "creditdetail"
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(Integer, index=True)
    creditnum = Column(Integer)  # 积分数额
    creditdesc = Column(String(500))  # 积分描述
    ctime = Column(DateTime)  # 记录时间


Base.metadata.create_all(bind=engine)
