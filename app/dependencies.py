from .sql.database import SessionLocal, SessionLocal_slave

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_slave_db():
    db = SessionLocal_slave()
    try:
        yield db
    finally:
        db.close()
