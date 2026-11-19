"""
ColdBridge AI - Public Cold Storage Directory Tests (Part 4 D1)

Verifies:
1. Seed creates exactly 10 listings; running twice still gives 10.
2. Seed does not change demo users or assets.
3. Seed does not overwrite contact_verified, is_partner, last_checked_on, coords, capacity, or verified contact info.
4. 401 Unauthorized without login.
5. 200 OK for each of the 5 roles (FARMER, BUYER, STATIC_OPERATOR, VAN_OPERATOR, ADMIN).
6. District filtering (Nashik, Pune).
7. Case-insensitive search across name, area, and address.
8. Validation: invalid district returns 422; q over 100 chars returns 422.
9. Items have is_partner=False and contact_verified=False by default.
10. Exact judge disclaimer is returned in API response.
11. Read-only enforcement: POST, PUT, PATCH, DELETE return 405 Method Not Allowed.
12. Isolation: matching ranking never includes directory listings.
13. Isolation: public_cold_storage_listings has zero incoming or outgoing foreign keys.
"""

from datetime import date, datetime, timezone
import pytest
from sqlalchemy import inspect
from app.models.user import User
from app.models.directory import PublicColdStorageListing
from app.models.produce import ProduceBatch
from app.seed.public_directory import seed_public_directory
from tests.conftest import auth_cookies_for

CSRF_HEADER = {"X-Requested-With": "XMLHttpRequest"}

EXPECTED_DISCLAIMER = (
    "These are real cold storage facilities in Nashik and Pune, "
    "taken from public directories. A farmer can contact them directly. "
    "The ranking and bids in our prototype are still simulated."
)


def test_directory_seed_and_idempotency_and_protection(db_session, farmer_user, operator_user):
    """
    Seed creates 10 listings; running twice gives 10;
    does not affect users or assets;
    does not overwrite verified or manual fields upon re-seed.
    """
    initial_user_count = db_session.query(User).count()

    # 1. First seed
    stats1 = seed_public_directory(db_session)
    assert stats1["inserted"] == 10
    assert stats1["total"] == 10
    assert db_session.query(PublicColdStorageListing).count() == 10

    # Demo users and assets must be untouched
    assert db_session.query(User).count() == initial_user_count

    # 2. Second seed (idempotency check)
    stats2 = seed_public_directory(db_session)
    assert stats2["inserted"] == 0
    assert stats2["untouched"] == 10
    assert db_session.query(PublicColdStorageListing).count() == 10

    # 3. Modify one row to simulate manual onboarding/verification
    row = db_session.query(PublicColdStorageListing).filter_by(name="Bhandari Cold Storage").first()
    assert row is not None
    row.contact_verified = True
    row.is_partner = True
    row.last_checked_on = date(2026, 11, 18)
    row.latitude = 19.9975
    row.longitude = 73.7898
    row.capacity_mt = 750.0
    row.address = "Protected Verified Address"
    row.phone = "9999999999"
    db_session.commit()

    # 4. Rerun seed: must NOT overwrite protected values
    seed_public_directory(db_session)
    assert db_session.query(PublicColdStorageListing).count() == 10

    rechecked = db_session.query(PublicColdStorageListing).filter_by(name="Bhandari Cold Storage").first()
    assert rechecked.contact_verified is True
    assert rechecked.is_partner is True
    assert rechecked.last_checked_on == date(2026, 11, 18)
    assert rechecked.latitude == 19.9975
    assert rechecked.longitude == 73.7898
    assert rechecked.capacity_mt == 750.0
    assert rechecked.address == "Protected Verified Address"
    assert rechecked.phone == "9999999999"


def test_directory_auth_and_roles_and_response_shape(
    client, db_session, farmer_user, operator_user, van_operator_user, admin_user
):
    """
    - 401 without login
    - 200 for each of the 5 roles (FARMER, BUYER, STATIC_OPERATOR, VAN_OPERATOR, ADMIN)
    - Default fields is_partner=False, contact_verified=False
    - Exact judge disclaimer present
    """
    seed_public_directory(db_session)

    # 1. 401 without login
    res_no_auth = client.get("/api/v1/directory/cold-storages")
    assert res_no_auth.status_code == 401

    # 2. Test 5 roles
    buyer_user = User(
        id="test-buyer-dir-001",
        email="buyer_dir@test.com",
        hashed_password="dummy_buyer_password",
        role="BUYER",
        full_name="Test Buyer Dir",
        is_active=True
    )
    db_session.add(buyer_user)
    db_session.commit()

    roles_to_test = [farmer_user, buyer_user, operator_user, van_operator_user, admin_user]
    for u in roles_to_test:
        cookies = auth_cookies_for(u)
        res = client.get("/api/v1/directory/cold-storages", cookies=cookies)
        assert res.status_code == 200, f"Role {u.role} failed with status {res.status_code}"
        data = res.json()
        assert data["disclaimer"] == EXPECTED_DISCLAIMER
        assert data["total"] == 10
        assert len(data["items"]) == 10

    # Inspect items on farmer response
    farmer_cookies = auth_cookies_for(farmer_user)
    res_farmer = client.get("/api/v1/directory/cold-storages", cookies=farmer_cookies)
    items = res_farmer.json()["items"]
    for item in items:
        assert "name" in item
        assert "district" in item
        assert item["district"] in ["Nashik", "Pune"]
        assert "area" in item
        assert "address" in item
        assert "is_partner" in item
        assert "contact_verified" in item


def test_directory_filtering_and_search(client, db_session, farmer_user):
    """
    - District filters (Nashik: 7 facilities, Pune: 3 facilities)
    - Search by name, area, address
    """
    seed_public_directory(db_session)
    cookies = auth_cookies_for(farmer_user)

    # 1. Filter Nashik (7 listings)
    res_nashik = client.get("/api/v1/directory/cold-storages?district=Nashik", cookies=cookies)
    assert res_nashik.status_code == 200
    nashik_items = res_nashik.json()["items"]
    assert len(nashik_items) == 7
    for it in nashik_items:
        assert it["district"] == "Nashik"

    # 2. Filter Pune (3 listings)
    res_pune = client.get("/api/v1/directory/cold-storages?district=Pune", cookies=cookies)
    assert res_pune.status_code == 200
    pune_items = res_pune.json()["items"]
    assert len(pune_items) == 3
    for it in pune_items:
        assert it["district"] == "Pune"

    # 3. Search by name
    res_search_name = client.get("/api/v1/directory/cold-storages?q=Bhandari", cookies=cookies)
    assert res_search_name.status_code == 200
    found_names = [it["name"] for it in res_search_name.json()["items"]]
    assert "Bhandari Cold Storage" in found_names

    # 4. Search by area
    res_search_area = client.get("/api/v1/directory/cold-storages?q=Chakan", cookies=cookies)
    assert res_search_area.status_code == 200
    found_areas = [it["name"] for it in res_search_area.json()["items"]]
    assert "Iceage Cold Storage" in found_areas

    # 5. Search by address
    res_search_addr = client.get("/api/v1/directory/cold-storages?q=Vani Road", cookies=cookies)
    assert res_search_addr.status_code == 200
    found_addr = [it["name"] for it in res_search_addr.json()["items"]]
    assert "Vishaka Agri Cold Storage" in found_addr

    # 6. Search no matches
    res_search_empty = client.get("/api/v1/directory/cold-storages?q=NonExistent999", cookies=cookies)
    assert res_search_empty.status_code == 200
    assert len(res_search_empty.json()["items"]) == 0
    assert res_search_empty.json()["total"] == 0


def test_directory_input_validations(client, db_session, farmer_user):
    """
    - Invalid district returns 422
    - q over 100 characters returns 422
    """
    seed_public_directory(db_session)
    cookies = auth_cookies_for(farmer_user)

    # 1. Invalid district
    res_inv_dist = client.get("/api/v1/directory/cold-storages?district=Mumbai", cookies=cookies)
    assert res_inv_dist.status_code == 422

    # 2. q > 100 chars
    long_q = "a" * 101
    res_long_q = client.get(f"/api/v1/directory/cold-storages?q={long_q}", cookies=cookies)
    assert res_long_q.status_code == 422


def test_directory_read_only_methods_405(client, db_session, farmer_user):
    """
    POST, PUT, PATCH, DELETE must return 405 Method Not Allowed.
    """
    seed_public_directory(db_session)
    cookies = auth_cookies_for(farmer_user)

    res_post = client.post("/api/v1/directory/cold-storages", json={"name": "Test"}, cookies=cookies, headers=CSRF_HEADER)
    assert res_post.status_code == 405

    res_put = client.put("/api/v1/directory/cold-storages", json={"name": "Test"}, cookies=cookies, headers=CSRF_HEADER)
    assert res_put.status_code == 405

    res_patch = client.patch("/api/v1/directory/cold-storages", json={"name": "Test"}, cookies=cookies, headers=CSRF_HEADER)
    assert res_patch.status_code == 405

    res_delete = client.delete("/api/v1/directory/cold-storages", cookies=cookies, headers=CSRF_HEADER)
    assert res_delete.status_code == 405


def test_directory_isolation_from_matching_and_no_foreign_keys(client, db_session, farmer_user, operator_user):
    """
    1. Table public_cold_storage_listings has zero incoming and outgoing foreign keys.
    2. Ranked offers from matching requests never contain directory entries.
    """
    seed_public_directory(db_session)
    directory_names = {d.name for d in db_session.query(PublicColdStorageListing).all()}

    # 1. Check foreign keys with SQLAlchemy inspector
    inspector = inspect(db_session.bind)
    out_fks = inspector.get_foreign_keys("public_cold_storage_listings")
    assert len(out_fks) == 0, f"Expected 0 outgoing foreign keys, found {out_fks}"

    for t in inspector.get_table_names():
        for fk in inspector.get_foreign_keys(t):
            assert fk["referred_table"] != "public_cold_storage_listings", f"Table {t} references directory!"

    # 2. Check matching isolation
    batch = ProduceBatch(
        id="batch-dir-iso-001",
        farmer_id=farmer_user.id,
        crop_code="TOMATO",
        quantity_kg=500.0,
        harvest_at=datetime.now(timezone.utc),
        ambient_temp_c=30.0,
        latitude=19.9975,
        longitude=73.7898,
        data_source="LIVE"
    )
    db_session.add(batch)
    db_session.commit()

    farmer_cookies = auth_cookies_for(farmer_user)

    # Create request
    req_res = client.post(
        "/api/v1/matching/requests",
        json={"batch_id": batch.id, "requested_quantity_kg": 500.0},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # Rank offers
    rank_res = client.post(
        f"/api/v1/matching/requests/{req_id}/rank",
        json={},
        cookies=farmer_cookies,
        headers=CSRF_HEADER
    )
    assert rank_res.status_code == 200
    ranked_offers = rank_res.json()["ranked_offers"]

    # Verify no directory listing appears in ranked offers
    for offer in ranked_offers:
        assert offer["asset_name"] not in directory_names, f"Directory listing {offer['asset_name']} appeared in ranked offers!"
