# app/services/database.py
from src.utils.commonImports import *
from src.utils.config import settings
from sqlalchemy.ext.asyncio import async_engine_from_config

class DatabaseSessionManager:
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker] = None

    def init(self, host: str):
        self._engine = create_async_engine(
            host,
            pool_pre_ping=True,
            echo=True,
            connect_args={"check_same_thread": False}  # This is crucial for SQLite
            )

        self._sessionmaker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self._engine
        )

    async def close(self):
        if self._engine is None:
            raise Exception("Database Session Manager is not initialized")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("Database Session Manager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception as ex:
                await connection.rollback()
                print(f"Error during connection: {ex}")  # Add logging
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("Database Session Manager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception as ex:
            await session.rollback()
            print(f"Error during session: {ex}")  # Add logging
            raise
        finally:
            await session.close()

    async def create_all(self, connection: AsyncConnection):
        await connection.run_sync(Base.metadata.create_all)

    async def drop_all(self, connection: AsyncConnection):
        await connection.run_sync(Base.metadata.drop_all)

DATABASE_URL = settings.database_url.replace("sqlite://", "sqlite+aiosqlite://")

sessionmanager = DatabaseSessionManager()
sessionmanager.init(DATABASE_URL)

async def get_session():
    async with sessionmanager.session() as session:
        yield session
