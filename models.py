from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username='{self.username}')>"

class DownloadRequest(Base):
    __tablename__ = "download_requests"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    youtube_url = Column(String(500), nullable=False)
    video_title = Column(String(300))
    video_duration = Column(Float)
    format_type = Column(String(10), default="mp4")  # mp4, mp3, webm
    quality = Column(String(20), default="best")
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    file_path = Column(String(500))
    file_size = Column(Integer)
    download_url = Column(String(500))
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<DownloadRequest(id={self.id}, url='{self.youtube_url}', status='{self.status}')>"

class DownloadStats(Base):
    __tablename__ = "download_stats"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    total_downloads = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)  # in bytes
    last_download = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DownloadStats(user_id={self.user_id}, downloads={self.total_downloads})>" 