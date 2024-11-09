# schemas.py
# Standard library imports
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime
from typing import List, Optional,Dict,Literal,Tuple

# Third party imports
from pydantic import BaseModel, ConfigDict, EmailStr

class Faces(BaseModel):
    """ This is a pydantic model to define the structure of the streaming data 
    that we will be sending to the cv2 Classifier to make predictions.
    It expects a List of a Tuple of 4 integers.
    """
    faces: List[Tuple[int, int, int, int]]

# User schemas
class UserBase(BaseModel):
    fullname: str | None = None
    role: str
    email: EmailStr
    phone_no: str 
    is_active: bool 
    #OAuth fields
    provider: str | None = None
    provider_id: str | None = None
    avatar_url: str | None = None 

class UserCreate(UserBase):
    password: str |None = None

class UserUpdate(BaseModel):
    fullname: str | None = None
    role: str | None = None
    phone_no: str | None = None
    email:str | None = None
    is_active: bool

    # OAuth fields
    provider: str | None = None
    provider_id: str | None = None
    avatar_url:str | None = None


class UserInDB(UserBase):
    user_id: UUID
    password: str
    created_at: datetime
    updated_at: datetime

class UserOut(UserBase):
    user_id: UUID 
    password:str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChangePassword(BaseModel):
    email: EmailStr
    new_password:str
    
# Token schemas
class TokenBase(BaseModel):
    user_id:UUID 
    access_token: str
    refresh_token: str
    status: bool

class TokenCreate(TokenBase):
    user_id: UUID 

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenOut(TokenBase):
    token_id:UUID
    created_at: datetime
    exp: int  # Unix timestamp for expiration
    model_config = ConfigDict(from_attributes=True)

#schema for creating a new sensor data entry
class SensorDataCreate(BaseModel):
    device_id:UUID |None=None
    mq5_level: int | None = None
    motion_status:int| None = None
    temperature:float | None = None
    humidity:int| None = None

# Pydantic schema for updating an existing sensor data entry
class SensorDataUpdate(BaseModel):
    mq5_level: Optional[float] = None
    motion_status: Optional[int] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None

# Pydantic schema for output/response when retrieving sensor data
class SensorDataOut(BaseModel):
    data_id: UUID
    device_id: UUID
    mq5_level: Optional[float]
    motion_status: Optional[int]
    temperature: Optional[float]
    humidity: Optional[float]
    recorded_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema for output with related device information
class SensorDataWithRelations(SensorDataOut):
    device: 'DeviceOut'  # Replace 'DeviceOut' with your actual device schema class if defined elsewhere
    model_config = ConfigDict(from_attributes=True)

# Pydantic schema for creating a new device entry
class DeviceCreate(BaseModel):
    device_name: str
    device_model: Optional[str] = None
    location: Optional[str] = None  # Where the device is placed (e.g., "Living Room", "Kitchen")

# Pydantic schema for updating an existing device entry
class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    device_model: Optional[str] = None
    location: Optional[str] = None

# Pydantic schema for output/response when retrieving device data
class DeviceOut(BaseModel):
    device_id: UUID
    device_name: str
    device_model: Optional[str]
    location: Optional[str]
    registered_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

# Schema for output with related sensor data information
class DeviceWithSensorData(DeviceOut):
    sensor_data: List['SensorDataOut']  # Replace with the actual import if necessary
    model_config = ConfigDict(from_attributes=True)
