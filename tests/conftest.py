import sys
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.security import hash_password, create_access_token
from app.models.user import User, FarmerProfile, OperatorProfile

# Use an isolated test database
TEST_DB_URL = "sqlite:///./test_coldbridge.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_db_file = Path("test_coldbridge.db")
    if test_db_file.exists():
        try:
            test_db_file.unlink()
        except Exception:
            pass

@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def farmer_user(db_session):
    user = User(
        id="test-farmer-001",
        email="farmer@test.com",
        hashed_password=hash_password("FarmerTest123!"),
        role="FARMER",
        full_name="Test Farmer",
        phone="+91-9876543210",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(FarmerProfile(
        user_id=user.id,
        farm_name="Test Farm",
        district="Nashik",
        state="Maharashtra"
    ))
    db_session.commit()
    return user

@pytest.fixture
def operator_user(db_session):
    from app.models.asset import ColdAsset, StaticAssetDetail
    user = User(
        id="test-operator-001",
        email="operator@test.com",
        hashed_password=hash_password("OperatorTest123!"),
        role="STATIC_OPERATOR",
        full_name="Test Operator",
        phone="+91-9876543211",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(OperatorProfile(
        user_id=user.id,
        business_name="Test Cold Chain",
        district="Pune",
        state="Maharashtra"
    ))
    db_session.flush()
    asset = ColdAsset(
        id="test-op-asset-001",
        operator_id=user.id,
        name="Nashik Cold Storage",
        asset_type="STATIC",
        total_capacity_kg=5000.0,
        available_capacity_kg=4000.0,
        price_per_kg_per_day=1.5,
        latitude=19.9975,
        longitude=73.7898,
        is_active=True
    )
    db_session.add(asset)
    db_session.flush()
    db_session.add(StaticAssetDetail(
        asset_id=asset.id,
        supported_crops="tomato, onion, mango",
        min_temperature_c=2.0,
        max_temperature_c=12.0
    ))
    db_session.commit()
    return user

@pytest.fixture
def van_operator_user(db_session):
    user = User(
        id="test-van-operator-001",
        email="vanop@test.com",
        hashed_password=hash_password("VanOpTest123!"),
        role="VAN_OPERATOR",
        full_name="Test Van Operator",
        phone="+91-9876543212",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(OperatorProfile(
        user_id=user.id,
        business_name="Test Van Fleet",
        district="Nashik",
        state="Maharashtra"
    ))
    db_session.commit()
    return user

@pytest.fixture
def admin_user(db_session):
    user = User(
        id="test-admin-001",
        email="admin@test.com",
        hashed_password=hash_password("AdminTest123!"),
        role="ADMIN",
        full_name="Test Admin",
        phone="+91-9876543299",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

def auth_cookies_for(user: User):
    token = create_access_token(data={"sub": user.id, "role": user.role})
    return {"access_token": token}
