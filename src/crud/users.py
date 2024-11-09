from src.utils.commonImports import *
from src.models import model
from src.schemas import schemas
from src.utils.commonSession import get_session
from src.utils import config
from pydantic import  EmailStr

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authenticate")

async def create_user(
    db: AsyncSession,
    user: schemas.UserCreate,
    hashed_password: Optional[str] = None,
    provider: Optional[str] = None,
    provider_id: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> schemas.UserOut:
    # Check if a user with this email already exists
    existing_user = await db.scalar(select(model.User).where(model.User.email == user.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered, please login",
        )
    # Create the user object
    db_user = model.User(
        fullname=user.fullname,
        role=user.role,
        email=user.email,
        phone_no=user.phone_no,
        password=hashed_password,
        is_active=user.is_active,
        provider=provider,
        provider_id=provider_id,
        avatar_url=avatar_url,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return schemas.UserOut.model_validate(db_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered, please login",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Function to get the current user based on the JWT token
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_session)
    )->schemas.UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            config.settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[config.settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        exp: int = payload.get("exp")
        provider_id: Optional[str] = payload.get("provider_id")

        if user_id is None or exp is None:
            raise credentials_exception

        # Check token expiration
        if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except (jwt.PyJWTError, ValidationError):
        raise credentials_exception

    # Query the database to retrieve the user based on either user_id or provider_id
    stmt = select(model.User).where(model.User.user_id == UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )

    # Return the UserOut schema using model_validate
    return schemas.UserOut.model_validate(user)  # Validate and convert the SQLAlchemy model to Pydantic schema


# Function to get the current active user
async def get_current_active_user(
    current_user: Annotated[schemas.UserOut, Depends(get_current_user)]
    ) -> schemas.UserOut:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_user(db: AsyncSession, user_id: UUID) -> Optional[model.User]:
    """
    Retrieves a user from the database by their ID.
    """
    result = await db.execute(select(model.User).where(model.User.user_id == user_id))
    user = result.scalar_one_or_none()
    return user  # Return the model object


async def update_user(
    db: AsyncSession, user_id: UUID, user_update: schemas.UserUpdate
    ) -> Optional[schemas.UserOut]:
    """
    Update a user's information.
    """
    result = await db.execute(select(model.User).where(model.User.user_id == user_id))
    db_user = result.scalar_one_or_none()

    if not db_user:
        return None

    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db_user.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(db_user)
        return schemas.UserOut.model_validate(db_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

async def update_user_by_email(
    db: AsyncSession, email: str, user_update: schemas.UserUpdate
) -> Optional[schemas.UserOut]:
    """
    Update a user's information based on their email.
    """
    # Query to get the user by email
    result = await db.execute(select(model.User).where(model.User.email == email))
    db_user = result.scalar_one_or_none()

    if not db_user:
        return None  # Return None if no user is found with the provided email

    # Update the user's data
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    # Update the updated_at timestamp
    db_user.updated_at = datetime.now(timezone.utc)

    try:
        # Commit the changes to the database
        await db.commit()
        # Refresh the session to get the updated user data
        await db.refresh(db_user)
        return schemas.UserOut.model_validate(db_user)
    except Exception as e:
        # Rollback if there's an error and raise an HTTP exception
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


async def get_user_by_email(db: AsyncSession, email: EmailStr) -> model.User:
    """
    Retrieve a user from the database by their email address (case-insensitive).
    """
    result = await db.execute(
        select(model.User).where(func.lower(model.User.email) == func.lower(email))
    )
    user = result.scalar_one_or_none()
    return user  # Return the actual user model object directly

# function to check if a user exists by email or phone number
async def get_user_by_email_or_phone(db: AsyncSession, email: EmailStr = None, phone_no: str = None) -> Optional[model.User]:
    query = select(model.User).where(
        (model.User.email == email) | (model.User.phone_no == phone_no)
    )

    result = await db.execute(query)
    user = result.scalar_one_or_none()
    return user

async def get_users(
    db: AsyncSession, skip: int = 1, limit: int = 100
    ) -> List[schemas.UserOut]:
    """
    Get a list of users with pagination.
    """
    result = await db.execute(select(model.User).offset(skip).limit(limit))
    users = result.scalars().all()
    return [schemas.UserOut.model_validate(user) for user in users]