import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

class ChatRecord(Base):
    __tablename__ = 'chat_records'
    id = Column(Integer, primary_key=True)
    user_message = Column(Text, nullable=False)
    bot_reply = Column(Text, nullable=False)

# Guardrail: Initialize engine lazily to ensure environment is fully loaded First
_engine = None
_SessionLocal = None

def init_db():
    global _engine, _SessionLocal
    if _engine is not None:
        return
        
    db_url = os.environ.get("DB_URL")
    if not db_url:
        logger.warning("DB_URL not found, falling back to SQLite for local development.")
        db_url = "sqlite:///./local_chat.db"
        _engine = create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        _engine = create_engine(db_url)
        
    Base.metadata.create_all(bind=_engine)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

async def save_chat_history(user_msg: str, bot_reply: str):
    """
    Saves a chat history record to the database (Cloud SQL or fallback).
    """
    if _SessionLocal is None:
        init_db()
        
    db = _SessionLocal()
    try:
        record = ChatRecord(user_message=user_msg, bot_reply=bot_reply)
        db.add(record)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save chat to DB: {str(e)}")
        db.rollback()
    finally:
        db.close()
