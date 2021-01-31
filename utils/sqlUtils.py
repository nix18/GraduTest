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


# Base是用来给模型类继承的，类似django中的models.Model
# 模型类，tablename指表名，如果数据库中没有这个表会自动创建，有表则会沿用
class qiandao(Base):
    __tablename__ = "qiandao"
    qd_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uid = Column(Integer)
    qd_time = Column(DateTime)


class tokenList(Base):
    __tablename__ = "tokenList"
    uid = Column(Integer, primary_key=True, index=True)
    token = Column(String(40))
    expire_time = Column(DateTime)


Base.metadata.create_all(bind=engine)
