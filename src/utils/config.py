# config.py
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, EmailStr, SecretStr, BeforeValidator, HttpUrl, TypeAdapter
from typing import List, Annotated

# Load environment variables from .env file
load_dotenv()


http_url_adapter = TypeAdapter(HttpUrl)

Url = Annotated[str, BeforeValidator(lambda value: str(http_url_adapter.validate_python(value)))]


class Settings(BaseSettings):
    # Database settings
    EXTERNAL_DATABASE_URL: str = Field(default=os.getenv("EXTERNAL_DATABASE_URL"))
  
    # API settings
    API_KEY: SecretStr = Field(default=os.getenv("API_KEY"))
    APP_NAME: str = Field(default=os.getenv("APP_NAME"))
    ADMIN_EMAIL: EmailStr = Field(default=os.getenv("ADMIN_EMAIL"))

    # JWT settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440)))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 10080)))
    JWT_ALGORITHM: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"))
    JWT_SECRET_KEY: SecretStr = Field(default=os.getenv("JWT_SECRET_KEY"))
    JWT_REFRESH_SECRET_KEY: SecretStr = Field(default=os.getenv("JWT_REFRESH_SECRET_KEY"))

    # Optional settings
    DEBUG: bool = Field(default=os.getenv("DEBUG", "False").lower() == "true")

    #Google Api Settings
    GOOGLE_CLIENT_ID:str = Field(default=os.getenv("GOOGLE_CLIENT_ID"))
    GOOGLE_CLIENT_SECRET:SecretStr = Field(default=os.getenv("GOOGLE_CLIENT_SECRET"))
    GOOGLE_REDIRECT_URI:Url=Field(default=os.getenv("GOOGLE_REDIRECT_URI"))
    GOOGLE_AUTH_URL:Url=Field(default=os.getenv("GOOGLE_AUTH_URL"))
    GOOGLE_TOKEN_URL:Url=Field(default=os.getenv("GOOGLE_TOKEN_URL"))
    GOOGLE_USER_INFO_URL:Url=Field(default=os.getenv("GOOGLE_USER_INFO_URL"))
    
    @property
    def database_url(self) -> str:
        if not all([self.EXTERNAL_DATABASE_URL]):
            raise ValueError("One or more required environment variables are missing or empty.")
        
        return (
            f"{self.EXTERNAL_DATABASE_URL}"
        )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a global instance of the Settings
settings = Settings()

# Function to get the settings
def get_settings():
    return settings