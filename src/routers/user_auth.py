import random
import re
from pydantic import  EmailStr
from src.utils.commonImports import *
from src.utils.commonSession import get_session
from src.crud.users import get_current_active_user
from src.schemas import schemas
from src.models import model
from src.utils import auth,config
from src import crud
import secrets


router = APIRouter(prefix="/user", tags=["user"])

#handle logging reports
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Function to normalize phone numbers (removes non-numeric characters and trims spaces)
def normalize_phone_number(phone_number: str) -> str:
    return re.sub(r'\D', '', phone_number).strip()

@router.post("/register")
async def register_user(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_session)):

    # Hash the password
    hashed_password = auth.get_hashed_password(user_in.password)
    
    # Create the user in the database
    created_user = await crud.users.create_user(db, user_in, hashed_password)
    return created_user


#endpoint to authenticate user
@router.post("/authenticate", summary="Create access and refresh tokens for user", response_model=schemas.TokenOut)
async def authenticate(payload: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    logger.info(f"Login attempt from email: {payload.username}")

    try:
        user = await crud.users.get_user_by_email(db=db, email=payload.username)
        if user is None:
            logger.warning(f"Login failed: User not found for email {payload.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if not auth.verify_password(payload.password, user.password):
            logger.warning(f"Login failed: Invalid password for user {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # create access and refresh token
        access_token = auth.create_access_token(subject=str(user.user_id))
        refresh_token = auth.create_refresh_token(subject=str(user.user_id))

        # Create and save token data
        token_db = model.Token(user_id=user.user_id, access_token=access_token, refresh_token=refresh_token, status=True)
        db.add(token_db)
        await db.commit()
        await db.refresh(token_db)

        logger.info(f"Login successful for user: {user.email}")
        
        return schemas.TokenOut(
            token_id=token_db.token_id,
            user_id=user.user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            status=token_db.status,
            created_at=token_db.created_at,
            exp=int((token_db.created_at + timedelta(days=30)).timestamp())
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login for email {payload.username}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")

@router.post("/refresh", summary="Refresh access token")
async def refresh_token(request: schemas.TokenRefreshRequest, db: AsyncSession = Depends(get_session)):
    try:
        payload = jwt.decode(
            request.refresh_token,
            config.settings.JWT_REFRESH_SECRET_KEY.get_secret_value(),
            algorithms=[config.settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Check for token expiration (optional)
        if jwt.get_current_jwt() is not None and jwt.get_current_jwt().has_expired_signature():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is expired")
        
        # Verify if the user exists and is active
        user = await crud.users.get_user(db=db, user_id=user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        # Create a new access token
        new_access_token = auth.create_access_token(subject=user_id)
        return {"access_token": new_access_token, "token_type": "bearer"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception as e:
        # Optionally log the unexpected error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")

@router.get('/email', response_model=schemas.UserOut)
async def fetch_user_by_email(email: EmailStr, db: AsyncSession = Depends(get_session)):
    """
    Fetch a user from the database by their email address.
    """
    try:
        # Fetch the user using the provided function
        user = await crud.users.get_user_by_email(db, email)
        
        # If the user does not exist, raise a 404 error
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while fetching the user")

# User change password endpoint
@router.post('/change-password', response_model=None)
async def change_password(
    request: schemas.ChangePassword,
    db: AsyncSession = Depends(get_session)
    ):
    try:
        # Fetch the user from the database to get the latest data
        logger.info(f"Fetching user with ID: {request.email}")
        user_result = await db.execute(select(model.User).where(model.User.email == request.email))
        user = user_result.scalars().first()

        if not user:
            logger.error(f"User with ID {request.email} not found in the database")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find user")

        # Update password
        user.password = auth.get_hashed_password(request.new_password)
        db.add(user)  
        await db.commit()

        logger.info(f"User: {user.email} successfully changed password")
        return {"message": "Password changed successfully"}

    except Exception as e:
        logger.error(f"Error changing password: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error changing password")


# Logout endpoint
@router.post("/logout")
async def logout(token: Annotated[str, Depends(crud.users.oauth2_scheme)], db: AsyncSession = Depends(get_session)):
    # Retrieve the token from the database
    db_token = await crud.token.get_token(db, token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    # Update the token status to revoked
    updated_token = await crud.token.update_token_status(db, token, status=False)
    if not updated_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke token"
        )
    
    return {"detail": "Logout successful"}


#endpoint to handle google authentication
@router.get("/login/google")
async def login_google():
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": config.settings.GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": config.settings.GOOGLE_REDIRECT_URI,
        "state": state
    }
    url = f"{config.settings.GOOGLE_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return RedirectResponse(url)

@router.get("/auth/callback")
async def auth_callback(request: Request, db: AsyncSession = Depends(get_session)):
    # Extract the authorization code from the query parameters
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")

    # Exchange the authorization code for an access token
    async with AsyncClient() as client:
        token_response = await client.post(
            config.settings.GOOGLE_TOKEN_URL,
            data={
                "client_id": config.settings.GOOGLE_CLIENT_ID,
                "client_secret": config.settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": config.settings.GOOGLE_REDIRECT_URI,
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Could not retrieve token")

    # Extract access token from the token response
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token not found")

    # Use the access token to get user info from Google
    async with AsyncClient() as client:
        user_info_response = await client.get(
            config.settings.GOOGLE_USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if user_info_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Could not retrieve user info")

    # Parse user information from Google
    user_info = user_info_response.json()
    email = user_info.get("email")
    fullname = user_info.get("name")
    provider_id = user_info.get("id")
    avatar_url = user_info.get("picture")

    if not email or not provider_id:
        raise HTTPException(
            status_code=400, detail="Incomplete user information retrieved from Google"
        )

    # Check if the user exists in the database
    existing_user = await crud.users.get_user_by_email(db, email=email)
    if existing_user:
        # User exists, update with any new information from Google
        existing_user.fullname = fullname or existing_user.fullname
        existing_user.avatar_url = avatar_url or existing_user.avatar_url
        await db.commit()
        await db.refresh(existing_user)
    else:
        # If user does not exist, create a new one
        new_user = model.User(
            fullname=fullname,
            email=email,
            provider="google",
            provider_id=provider_id,
            avatar_url=avatar_url,
            is_active=True,
            createdAt=datetime.now(timezone.utc),
            updatedAt=datetime.now(timezone.utc),
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        existing_user = new_user

    # Generate a JWT token for the authenticated user
    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = jwt.encode(
        {
            "sub": str(existing_user.id),
            "exp": datetime.now(timezone.utc) + access_token_expires,
        },
        config.settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=config.settings.JWT_ALGORITHM,
    )

    # Redirect to your application's frontend with the token
    frontend_url = f"{config.settings.FRONTEND_URL}/?token={jwt_token}"
    return {"message": "Authentication successful", "redirect_url": frontend_url}

@router.get("/users", response_model=List[schemas.UserOut], status_code=status.HTTP_200_OK)
async def read_users(
    skip: int = 1, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_session),
    current_user:dict = Depends(get_current_active_user)
    ) -> List[schemas.UserOut]:
    """
    Get a list of users with pagination.
    """
    return await crud.users.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=schemas.UserOut, status_code=status.HTTP_200_OK)
async def read_user(user_id: UUID, db: AsyncSession = Depends(get_session)) -> schemas.UserOut:
    """
    Get a single user by their ID.
    """
    user = await crud.users.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=schemas.UserOut, status_code=status.HTTP_200_OK)
async def update_user_endpoint(
    user_id: UUID, 
    user_update: schemas.UserUpdate, 
    db: AsyncSession = Depends(get_session),
    current_user:dict = Depends(get_current_active_user)                          
    ) -> schemas.UserOut:
    """
    Update a user's information.
    """
    updated_user = await crud.users.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID, 
    db: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete a user by their ID.
    """
    # Retrieve the user from the database (this is a model instance, not a Pydantic schema)
    user = await crud.users.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        # Manually delete associated tokens before deleting the user
        await crud.token.delete_tokens_by_user_id(db, user_id)
        
        # Delete the user using the model instance
        await db.delete(user)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {str(e)}")
