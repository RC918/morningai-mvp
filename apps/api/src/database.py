import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 初始化 SQLAlchemy
db = SQLAlchemy()

# 設置資料庫連接
DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
