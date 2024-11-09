# model.py
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
from enum import Enum

# SQLAlchemy specific imports
from sqlalchemy import String, Boolean,Integer,Float, DateTime, ForeignKey,Table,Column,Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base


Base = declarative_base()


def get_current_utc_time():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "user"
    
    user_id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    fullname: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(250), unique=True, index=True)
    phone_no: Mapped[str] = mapped_column(String(16), unique=True)
    password: Mapped[Optional[str]] = mapped_column(String(128))  
    is_active: Mapped[bool] = mapped_column(default=False)

    # OAuth fields
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "google"
    provider_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., Google user ID
    avatar_url: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)  # Optional profile picture URL

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow
    )

    # One-to-Many relationships
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="owner")  # Relationship to devices owned by the user
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="receiver")  # Messages received by the user
  

class Token(Base):
    __tablename__ = "token"
    token_id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.user_id",ondelete='CASCADE'), nullable=False)
    access_token: Mapped[str] = mapped_column(String(450), primary_key=True,unique=True)
    refresh_token: Mapped[str] = mapped_column(String(450), nullable=False,unique=True)
    status: Mapped[bool] = mapped_column(default=True)  # True means active, False means revoked
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_utc_time)
    revoked_at: Mapped[Optional[datetime]] = None  

class SensorData(Base):
    __tablename__ = "sensor_data"

    data_id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    device_id: Mapped[UUID] = mapped_column(ForeignKey("device.device_id"), nullable=False)
    
    # MQ5 gas concentration level
    mq5_level: Mapped[Optional[int]] = mapped_column(Float, nullable=True)
    
    # PIR motion status (0 or 1)
    motion_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # DHT11 temperature and humidity readings
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity: Mapped[Optional[int]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

    # Updated relationship to Device
    device: Mapped["Device"] = relationship("Device", back_populates="sensor_data")

class Device(Base):
    __tablename__ = "device"
    
    device_id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_model: Mapped[str] = mapped_column(String(255), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    # Timestamps
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=True, onupdate=datetime.utcnow)

    # Relationship to the user (owner of the device)
    owner: Mapped["User"] = relationship("User", back_populates="devices")
    
    # Relationship to multiple sensor data entries
    sensor_data: Mapped[List["SensorData"]] = relationship("SensorData", back_populates="device", cascade="all, delete-orphan")
    
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="device")
  

class Message(Base):
    __tablename__ = "message"
    
    message_id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("device.device_id"), nullable=False)  # Sender is a device
    receiver_id: Mapped[UUID] = mapped_column(ForeignKey("user.user_id"), nullable=False)  # Receiver is a user
    
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)  # Fixed to String for content
    
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    device: Mapped["Device"] = relationship("Device", back_populates="messages")
    receiver: Mapped["User"] = relationship("User", back_populates="messages")