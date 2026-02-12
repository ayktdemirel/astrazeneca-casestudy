import pytest
import asyncio
from src.database import engine, Base
# Import models to register them with Base
from src.models import competitor, clinical_trial 

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    print("CREATING TABLES") # Debug
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    print("DROPPING TABLES") # Debug
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
