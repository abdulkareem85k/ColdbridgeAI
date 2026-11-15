import datetime
from datetime import timezone
import sys
from pathlib import Path

# Add backend directory to path if running directly
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User, FarmerProfile, OperatorProfile
from app.models.asset import ColdAsset, StaticAssetDetail, MobileAssetDetail, AssetAvailability
from app.models.produce import ProduceBatch, SpoilageAssessment
from app.models.matching import MatchingRequest, Bid
from app.models.booking import Booking
from app.core.security import hash_password

def seed_demo_data(db=None):
    """
    Seed deterministic demo data for Maharashtra (Nashik, Pune, Ratnagiri, Mumbai).
    Running this script multiple times produces the exact same deterministic dataset.
    All records are marked with data_source='SIMULATED'.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        # Ensure all tables exist
        Base.metadata.create_all(bind=engine)

        # Clear existing demo data cleanly in dependency order
        db.query(Booking).delete()
        db.query(Bid).delete()
        db.query(MatchingRequest).delete()
        db.query(SpoilageAssessment).delete()
        db.query(ProduceBatch).delete()
        db.query(AssetAvailability).delete()
        db.query(StaticAssetDetail).delete()
        db.query(MobileAssetDetail).delete()
        db.query(ColdAsset).delete()
        db.query(FarmerProfile).delete()
        db.query(OperatorProfile).delete()
        db.query(User).delete()
        db.commit()

        now = datetime.datetime.now(timezone.utc)
        demo_pw = "DemoPassword123!"

        # 1. USERS & PROFILES
        # Demo Farmer 1
        farmer1 = User(
            id="f1000000-0000-0000-0000-000000000001",
            email="farmer.demo@coldbridge.ai",
            hashed_password=hash_password("FarmerDemo123!"),
            role="FARMER",
            full_name="Ramesh Patil",
            phone="+91-9822011001",
            is_active=True
        )
        db.add(farmer1)
        db.flush()
        db.add(FarmerProfile(
            id="fp000000-0000-0000-0000-000000000001",
            user_id=farmer1.id,
            farm_name="Patil Agro Orchards",
            district="Nashik",
            state="Maharashtra",
            default_latitude=19.9975,
            default_longitude=73.7898
        ))

        # Additional Farmers (Total 5 Farmers)
        farmer2 = User(
            id="f1000000-0000-0000-0000-000000000002",
            email="suresh.farmer@coldbridge.ai",
            hashed_password=hash_password(demo_pw),
            role="FARMER",
            full_name="Suresh Shinde",
            phone="+91-9822011002",
            is_active=True
        )
        farmer3 = User(
            id="f1000000-0000-0000-0000-000000000003",
            email="anil.farmer@coldbridge.ai",
            hashed_password=hash_password(demo_pw),
            role="FARMER",
            full_name="Anil Deshmukh",
            phone="+91-9822011003",
            is_active=True
        )
        farmer4 = User(
            id="f1000000-0000-0000-0000-000000000004",
            email="vijay.farmer@coldbridge.ai",
            hashed_password=hash_password(demo_pw),
            role="FARMER",
            full_name="Vijay Pawar",
            phone="+91-9822011004",
            is_active=True
        )
        farmer5 = User(
            id="f1000000-0000-0000-0000-000000000005",
            email="mahesh.farmer@coldbridge.ai",
            hashed_password=hash_password(demo_pw),
            role="FARMER",
            full_name="Mahesh Kadam",
            phone="+91-9822011005",
            is_active=True
        )
        db.add_all([farmer2, farmer3, farmer4, farmer5])
        db.flush()

        db.add_all([
            FarmerProfile(id="fp000000-0000-0000-0000-000000000002", user_id=farmer2.id, farm_name="Shinde Tomato Farms", district="Pune", state="Maharashtra", default_latitude=18.5204, default_longitude=73.8567),
            FarmerProfile(id="fp000000-0000-0000-0000-000000000003", user_id=farmer3.id, farm_name="Ratnagiri Alphonso Estate", district="Ratnagiri", state="Maharashtra", default_latitude=16.9902, default_longitude=73.3120),
            FarmerProfile(id="fp000000-0000-0000-0000-000000000004", user_id=farmer4.id, farm_name="Pawar Vineyard", district="Nashik", state="Maharashtra", default_latitude=20.0110, default_longitude=73.8120),
            FarmerProfile(id="fp000000-0000-0000-0000-000000000005", user_id=farmer5.id, farm_name="Kadam Berry Grove", district="Mumbai", state="Maharashtra", default_latitude=19.0760, default_longitude=72.8777),
        ])

        # Demo Static Operator
        static_op = User(
            id="op000000-0000-0000-0000-000000000001",
            email="static.demo@coldbridge.ai",
            hashed_password=hash_password("StaticDemo123!"),
            role="STATIC_OPERATOR",
            full_name="Kisan Cold Storage Ltd",
            phone="+91-9822022001",
            is_active=True
        )
        db.add(static_op)
        db.flush()
        db.add(OperatorProfile(
            id="opp00000-0000-0000-0000-000000000001",
            user_id=static_op.id,
            business_name="Kisan Cold Storage Network",
            contact_phone="+91-9822022001",
            district="Pune",
            state="Maharashtra"
        ))

        # Demo Van Operator
        van_op = User(
            id="op000000-0000-0000-0000-000000000002",
            email="van.demo@coldbridge.ai",
            hashed_password=hash_password("VanDemo123!"),
            role="VAN_OPERATOR",
            full_name="SolarGlide Logistics",
            phone="+91-9822033001",
            is_active=True
        )
        db.add(van_op)
        db.flush()
        db.add(OperatorProfile(
            id="opp00000-0000-0000-0000-000000000002",
            user_id=van_op.id,
            business_name="SolarGlide Mobile Fleet",
            contact_phone="+91-9822033001",
            district="Nashik",
            state="Maharashtra"
        ))

        # Demo Admin
        admin_user = User(
            id="ad000000-0000-0000-0000-000000000001",
            email="admin.demo@coldbridge.ai",
            hashed_password=hash_password("AdminDemo123!"),
            role="ADMIN",
            full_name="System Administrator",
            phone="+91-9822099999",
            is_active=True
        )
        db.add(admin_user)
        db.flush()

        # 2. COLD ASSETS
        # 6 Static Cold Rooms
        static_rooms_data = [
            ("a1000000-0000-0000-0000-000000000001", "Nashik Agro Warehouse A", 5000.0, 3500.0, 1.5, 20.0050, 73.7950, "mango,tomato,grapes", 2.0, 12.0, "Pune-Nashik Rd, Nashik"),
            ("a1000000-0000-0000-0000-000000000002", "Godavari Cold Vault", 3000.0, 1800.0, 1.8, 20.0800, 73.8400, "grapes,pomegranate,onion", 0.0, 10.0, "Dindori Road, Nashik"),
            ("a1000000-0000-0000-0000-000000000003", "Sahyadri FPO Cold Room", 8000.0, 6000.0, 1.2, 18.1500, 74.5800, "tomato,onion,mango", 4.0, 15.0, "Baramati MIDC, Pune"),
            ("a1000000-0000-0000-0000-000000000004", "Pune Central Perishable Hub", 10000.0, 8500.0, 2.0, 18.5050, 73.9300, "mango,grapes,tomato,strawberry", 1.0, 12.0, "Hadapsar, Pune"),
            ("a1000000-0000-0000-0000-000000000005", "Konkan Mango Deep Freeze", 4000.0, 2500.0, 2.2, 16.9850, 73.3250, "mango,fish,cashew_apple", -2.0, 10.0, "Mirjole MIDC, Ratnagiri"),
            ("a1000000-0000-0000-0000-000000000006", "Mumbai Agro Aggregation Hub", 12000.0, 9000.0, 2.5, 19.2900, 73.0600, "mango,tomato,grapes,onion", 2.0, 14.0, "Bhiwandi Logistics Park, Mumbai"),
        ]

        for aid, name, tot_cap, avail_cap, price, lat, lng, crops, min_t, max_t, addr in static_rooms_data:
            asset = ColdAsset(
                id=aid,
                operator_id=static_op.id,
                name=name,
                asset_type="STATIC",
                total_capacity_kg=tot_cap,
                available_capacity_kg=avail_cap,
                price_per_kg_per_day=price,
                latitude=lat,
                longitude=lng,
                is_active=True,
                data_source="SIMULATED"
            )
            db.add(asset)
            db.flush()
            db.add(StaticAssetDetail(
                id=f"sd{aid[2:]}",
                asset_id=aid,
                supported_crops=crops,
                min_temperature_c=min_t,
                max_temperature_c=max_t,
                address=addr
            ))

        # 4 Mobile Vans with varying solar_reliability simulation inputs
        mobile_vans_data = [
            ("a2000000-0000-0000-0000-000000000001", "SolarVan Alpha", 1200.0, 800.0, 2.4, 20.0100, 73.7800, "MH-15-AB-1001", 60.0, 0.95),
            ("a2000000-0000-0000-0000-000000000002", "SolarVan Beta", 800.0, 800.0, 2.0, 18.5300, 73.8400, "MH-12-CD-2002", 45.0, 0.85),
            ("a2000000-0000-0000-0000-000000000003", "SolarVan Gamma", 1000.0, 750.0, 2.2, 16.9950, 73.3050, "MH-08-EF-3003", 50.0, 0.70),
            ("a2000000-0000-0000-0000-000000000004", "SolarVan Delta", 600.0, 400.0, 1.9, 19.1200, 72.8500, "MH-04-GH-4004", 40.0, 0.50),
        ]

        for aid, name, tot_cap, avail_cap, price, lat, lng, vref, radius, solar in mobile_vans_data:
            asset = ColdAsset(
                id=aid,
                operator_id=van_op.id,
                name=name,
                asset_type="MOBILE",
                total_capacity_kg=tot_cap,
                available_capacity_kg=avail_cap,
                price_per_kg_per_day=price,
                latitude=lat,
                longitude=lng,
                is_active=True,
                data_source="SIMULATED"
            )
            db.add(asset)
            db.flush()
            db.add(MobileAssetDetail(
                id=f"md{aid[2:]}",
                asset_id=aid,
                vehicle_ref=vref,
                service_radius_km=radius,
                solar_reliability=solar,  # Configurable simulation input
                last_location_at=now - datetime.timedelta(minutes=15)
            ))

        # 3. 12 PRODUCE BATCHES
        batches_data = [
            ("b0000000-0000-0000-0000-000000000001", farmer1.id, "mango", 500.0, now - datetime.timedelta(hours=4), 32.5, 19.9975, 73.7898, "Alphonso harvest - urgent farmgate pickup"),
            ("b0000000-0000-0000-0000-000000000002", farmer1.id, "tomato", 800.0, now - datetime.timedelta(hours=8), 34.0, 19.9800, 73.7700, "Ripe red tomatoes"),
            ("b0000000-0000-0000-0000-000000000003", farmer1.id, "grapes", 1200.0, now - datetime.timedelta(hours=14), 29.0, 20.0200, 73.8200, "Thompson seedless table grapes"),
            ("b0000000-0000-0000-0000-000000000004", farmer2.id, "tomato", 1500.0, now - datetime.timedelta(hours=6), 33.0, 18.5204, 73.8567, "Hybrid tomatoes morning harvest"),
            ("b0000000-0000-0000-0000-000000000005", farmer2.id, "onion", 2500.0, now - datetime.timedelta(hours=24), 31.0, 18.5500, 73.8700, "Red storage onions"),
            ("b0000000-0000-0000-0000-000000000006", farmer3.id, "mango", 600.0, now - datetime.timedelta(hours=5), 35.0, 16.9902, 73.3120, "Export grade Ratnagiri Alphonso"),
            ("b0000000-0000-0000-0000-000000000007", farmer3.id, "cashew_apple", 400.0, now - datetime.timedelta(hours=3), 33.5, 17.0100, 73.3300, "Extremely perishable cashew apples"),
            ("b0000000-0000-0000-0000-000000000008", farmer4.id, "grapes", 750.0, now - datetime.timedelta(hours=12), 28.5, 20.0110, 73.8120, "Sharad seedless black grapes"),
            ("b0000000-0000-0000-0000-000000000009", farmer4.id, "pomegranate", 900.0, now - datetime.timedelta(hours=18), 30.5, 20.0300, 73.8300, "Bhagwa pomegranates"),
            ("b0000000-0000-0000-0000-000000000010", farmer5.id, "strawberry", 350.0, now - datetime.timedelta(hours=2), 31.0, 19.0760, 72.8777, "Fresh harvested strawberries"),
            ("b0000000-0000-0000-0000-000000000011", farmer5.id, "tomato", 650.0, now - datetime.timedelta(hours=10), 32.0, 19.1000, 72.8900, "Greenhouse table tomatoes"),
            ("b0000000-0000-0000-0000-000000000012", farmer1.id, "pomegranate", 1100.0, now - datetime.timedelta(hours=22), 29.5, 19.9900, 73.8000, "Arakta pomegranates"),
        ]

        for bid_val, fid, crop, qty, harv_at, temp, lat, lng, notes in batches_data:
            batch = ProduceBatch(
                id=bid_val,
                farmer_id=fid,
                crop_code=crop,
                quantity_kg=qty,
                harvest_at=harv_at,
                ambient_temp_c=temp,
                latitude=lat,
                longitude=lng,
                notes=notes,
                data_source="SIMULATED"
            )
            db.add(batch)

        db.flush()

        # 4. MATCHING REQUEST & BIDS (Designed so Nearest, Cheapest, and ColdBridge picks differ)
        # Using batch 1 (Farmer 1, 500 kg mango, Nashik)
        # Option A (Nearest): Static room 1 (Nashik Agro Warehouse A) - 5 km, 65 min, Rs 1000
        # Option B (ColdBridge Pick): SolarVan Alpha - 8 km, 35 min, Rs 1200, solar 0.95 -> high urgency farmgate winner
        # Option C (Cheapest): Static room 2 (Godavari Cold Vault) - 25 km, 90 min, Rs 800
        req1 = MatchingRequest(
            id="mr000000-0000-0000-0000-000000000001",
            batch_id="b0000000-0000-0000-0000-000000000001",
            farmer_id=farmer1.id,
            requested_quantity_kg=500.0,
            status="MATCHED"
        )
        db.add(req1)
        db.flush()

        # 3 bids on request 1
        bids_data = [
            # A: Nearest room
            ("bd000000-0000-0000-0000-000000000001", req1.id, "a1000000-0000-0000-0000-000000000001", 1000.0, 1000.0, 65.0, now + datetime.timedelta(hours=2), 0.334, "Nearest static warehouse option"),
            # B: Mobile Van (ColdBridge Pick when high urgency)
            ("bd000000-0000-0000-0000-000000000002", req1.id, "a2000000-0000-0000-0000-000000000001", 800.0, 1200.0, 35.0, now + datetime.timedelta(hours=2), 0.297, "Fast mobile solar cooling dispatch"),
            # C: Cheapest static room
            ("bd000000-0000-0000-0000-000000000003", req1.id, "a1000000-0000-0000-0000-000000000002", 800.0, 800.0, 90.0, now + datetime.timedelta(hours=2), 0.444, "Budget economic storage option"),
        ]

        for bid_id, rid, aid, off_cap, prc, eta, v_until, sc, note in bids_data:
            db.add(Bid(
                id=bid_id,
                request_id=rid,
                asset_id=aid,
                offered_capacity_kg=off_cap,
                price_total=prc,
                eta_minutes=eta,
                valid_until=v_until,
                score=sc,
                note=note,
                data_source="SIMULATED",
                is_accepted=False,
                is_expired=False
            ))

        db.commit()
        print("Demo data seeded successfully with deterministic records.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    seed_demo_data()
