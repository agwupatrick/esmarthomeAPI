# commonImports.py

# Standard Library Imports
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
from typing import Annotated, Union, Any, List, Optional, AsyncIterator

# Third-Party Imports
from sqlalchemy.ext.asyncio import (
    AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
)
from sqlalchemy.exc import NoResultFound, IntegrityError,SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy import delete
from fastapi import Depends, HTTPException, status, APIRouter,Path,BackgroundTasks, WebSocket,Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from starlette.requests import Request
from httpx import AsyncClient
import jwt  
from jwt.exceptions import InvalidTokenError
import httpx
import logging
import secrets
import contextlib
import asyncio
import json
from typing import Annotated,Tuple,List,Dict

# Local Application Imports
from src.models.model import Base


