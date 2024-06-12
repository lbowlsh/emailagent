import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import create_engine, Column, String, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()


class CustomerInfo(BaseModel):
    thread_id: str
    sender: str
    content: str
    customer_name: str = Field(..., description="The name of the customer")
    contact_info: str = Field(..., description="The contact information of the customer")
    inquiry: str = Field(..., description="The specific inquiry from the customer")

class SalesOpportunity(BaseModel):
    opportunity_id: str = Field(..., description="The ID of the sales opportunity")
    need: str = Field(..., description="The specific need identified")
    opportunity: str = Field(..., description="The sales opportunity identified")

# 创建数据库模型
Base = declarative_base()




class CustomerInfoModel(Base):
    __tablename__ = "customer_info"
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(16))
    sender = Column(String(50))
    content = Column(String(50))
    customer_name = Column(String(50))
    contact_info = Column(String(50))
    inquiry = Column(String(255))

class SalesOpportunityModel(Base):
    __tablename__ = "sales_opportunity"
    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(String(50), primary_key=True, index=True)
    need = Column(Text)
    opportunity = Column(Text)

# Database configuration from environment variables
db_user = os.getenv('DB_USERNAME')
db_pass = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_port = os.getenv('DB_PORT')

# 正式环境数据连接配置
# app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:3306/{db_name}'

# 本地环境数据库连接配置
# app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@127.0.0.1:3506/{db_name}'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)

# MySQL连接配置
DATABASE_URL =f'mysql+pymysql://{db_user}:{db_pass}@127.0.0.1:{db_port}/{db_name}'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建表格
Base.metadata.create_all(bind=engine)
