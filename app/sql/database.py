from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json

DB_INFO = json.loads(os.environ['DB_INFO'])
DATEBASE_URL_FORMAT = 'mysql://{}:{}@{}:{}/{}?charset=utf8mb4'
MASTER_DATABASE_URL = DATEBASE_URL_FORMAT.format(
    DB_INFO['username'],
    DB_INFO['password'],
    DB_INFO['host'],
    int(DB_INFO['port']),
    DB_INFO['database']
)

SLAVE_DATABASE_URL = DATEBASE_URL_FORMAT.format(
    DB_INFO['username'],
    DB_INFO['password'],
    DB_INFO['slave_host'],
    int(DB_INFO['port']),
    DB_INFO['database']
)

engine = create_engine(MASTER_DATABASE_URL)
slave_engine = create_engine(SLAVE_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal_slave = sessionmaker(autocommit=False, autoflush=False, bind=slave_engine)

Base = declarative_base()
