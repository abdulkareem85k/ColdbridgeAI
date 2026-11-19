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
from app.models.user import User, FarmerProfile, OperatorProfile, BuyerProfile
from app.models.asset import ColdAsset, StaticAssetDetail, MobileAssetDetail, AssetAvailability
from app.models.produce import ProduceBatch, SpoilageAssessment
from app.models.matching import MatchingRequest, Bid
from app.models.booking import Booking
from app.models.inventory import Inventory, Alert
from app.models.marketplace import BuyerListing, PurchaseOrder
from app.models.forecast import DemandForecast
from app.core.security import hash_password
from app.services.marketplace_service import calculate_sliding_discount
from app.services.forecast_service import DEFAULT_SEASONAL_ESTIMATES

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
        # Ensure all tables exist on the active database
        target_bind = db.get_bind() if db else engine
        Base.metadata.create_all(bind=target_bind)

        # Clear existing demo data cleanly in dependency order
        db.query(PurchaseOrder).delete()
        db.query(BuyerListing).delete()
        db.query(Alert).delete()
        db.query(Inventory).delete()
        db.query(DemandForecast).delete()
        db.query(Booking).delete()
        db.query(Bid).delete()
        db.query(MatchingRequest).delete()
        db.query(SpoilageAssessment).delete()
        db.query(ProduceBatch).delete()
        db.query(AssetAvailability).delete()
        db.query(StaticAssetDetail).delete()
        db.query(MobileAssetDetail).delete()
        db.query(ColdAsset).delete()
        db.query(BuyerProfile).delete()
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
            email="santosh.farmer@coldbridge.ai",
            hashed_password=hash_password(demo_pw),
            role="FARMER",
            full_name="Santosh Gaikwad",
            phone="+91-9822011005",
            is_active=True
        )
        db.add_all([farmer2, farmer3, farmer4, farmer5])
        db.flush()

        db.add(FarmerProfile(
            id="fp000000-0000-0000-0000-000000000002",
            user_id=farmer2.id,
            farm_name="Shinde Agro Estates",
            district="Pune",
            state="Maharashtra",
            default_latitude=18.5204,
            default_longitude=73.8567
        ))
        db.add(FarmerProfile(
            id="fp000000-0000-0000-0000-000000000003",
            user_id=farmer3.id,
            farm_name="Konkan Alphonso Farms",
            district="Ratnagiri",
            state="Maharashtra",
            default_latitude=16.9902,
            default_longitude=73.3120
        ))
        db.add(FarmerProfile(
            id="fp000000-0000-0000-0000-000000000004",
            user_id=farmer4.id,
            farm_name="Sahyadri Vineyards",
            district="Nashik",
            state="Maharashtra",
            default_latitude=20.0000,
            default_longitude=73.8000
        ))
        db.add(FarmerProfile(
            id="fp000000-0000-0000-0000-000000000005",
            user_id=farmer5.id,
            farm_name="Gaikwad Berry Farm",
            district="Mumbai",
            state="Maharashtra",
            default_latitude=19.0760,
            default_longitude=72.8777
        ))

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
            business_name="Nashik Cold Chain Infrastructure",
            contact_phone="+91-9822022001",
            district="Nashik",
            state="Maharashtra"
        ))

        # Additional Operators
        static_op2 = User(
            id="op000000-0000-0000-0000-000000000003",
            email="pune.operator@coldbridge.ai",
            hashed_password=hash_password(demo_pw),
            role="STATIC_OPERATOR",
            full_name="Pune Perishable Hubs",
            phone="+91-9822022002",
            is_active=True
        )
        db.add(static_op2)
        db.flush()
        db.add(OperatorProfile(
            id="opp00000-0000-0000-0000-000000000003",
            user_id=static_op2.id,
            business_name="Western Maharashtra Cold Hubs",
            contact_phone="+91-9822022002",
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

        # Demo Buyer (Phase 2)
        buyer1 = User(
            id="u1000000-0000-0000-0000-000000000099",
            email="buyer.demo@coldbridge.ai",
            hashed_password=hash_password("BuyerDemo123!"),
            role="BUYER",
            full_name="Vikram Mehta",
            phone="+91-9822011999",
            is_active=True
        )
        db.add(buyer1)
        db.flush()
        db.add(BuyerProfile(
            id="bp000000-0000-0000-0000-000000000001",
            user_id=buyer1.id,
            business_name="Maharashtra Fresh Agro Wholesalers",
            buyer_type="WHOLESALER",
            district="Pune",
            state="Maharashtra",
            address="Plot 42, Gultekdi Market Yard, Pune"
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
                operator_id=static_op.id if ("Nashik" in name or "Godavari" in name) else static_op2.id,
                name=name,
                asset_type="STATIC",
                latitude=lat,
                longitude=lng,
                total_capacity_kg=tot_cap,
                available_capacity_kg=avail_cap,
                price_per_kg_per_day=price,
                is_active=True,
                data_source="SIMULATED"
            )
            db.add(asset)
            db.flush()
            db.add(StaticAssetDetail(
                id=f"sad{aid[3:]}",
                asset_id=asset.id,
                supported_crops=crops,
                min_temperature_c=min_t,
                max_temperature_c=max_t,
                address=addr
            ))

        # 4 Mobile Solar Vans
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
                latitude=lat,
                longitude=lng,
                total_capacity_kg=tot_cap,
                available_capacity_kg=avail_cap,
                price_per_kg_per_day=price,
                is_active=True,
                data_source="SIMULATED"
            )
            db.add(asset)
            db.flush()
            db.add(MobileAssetDetail(
                id=f"mad{aid[3:]}",
                asset_id=asset.id,
                vehicle_ref=vref,
                service_radius_km=radius,
                solar_reliability=solar,
                last_location_at=now
            ))

        # 3. PRODUCE BATCHES (12 batches across 5 farmers)
        batches_data = [
            ("b0000000-0000-0000-0000-000000000001", farmer1.id, "mango", 500.0, now - datetime.timedelta(hours=4), 32.0, 19.9975, 73.7898, "Kesar mangoes harvested early morning"),
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

        # 4. MATCHING REQUEST & BIDS (Deterministic Demo Match)
        req1 = MatchingRequest(
            id="mr000000-0000-0000-0000-000000000001",
            batch_id="b0000000-0000-0000-0000-000000000001",
            farmer_id=farmer1.id,
            requested_quantity_kg=500.0,
            status="MATCHED"
        )
        db.add(req1)
        db.flush()

        bids_data = [
            ("bd000000-0000-0000-0000-000000000001", req1.id, "a1000000-0000-0000-0000-000000000001", 1000.0, 1000.0, 65.0, now + datetime.timedelta(hours=2), 0.334, "Nearest static warehouse option"),
            ("bd000000-0000-0000-0000-000000000002", req1.id, "a2000000-0000-0000-0000-000000000001", 800.0, 1200.0, 35.0, now + datetime.timedelta(hours=2), 0.297, "Fast mobile solar cooling dispatch"),
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

        # 5. PHASE 2 SEED: Active Stored Inventory, Alerts & Surplus Listings
        # Demo Booking in IN_STORAGE state
        seed_booking = Booking(
            id="bk000000-0000-0000-0000-000000000001",
            request_id=req1.id,
            batch_id="b0000000-0000-0000-0000-000000000002", # 800 kg tomato
            asset_id="a1000000-0000-0000-0000-000000000001", # Nashik Agro Warehouse A
            farmer_id=farmer1.id,
            quantity_kg=800.0,
            status="IN_STORAGE",
            reserved_until=None,
            rate_per_kg_per_day=1.5,
            days_estimated=5,
            estimated_total_inr=6000.0,
            status_updated_by=static_op.id
        )
        db.add(seed_booking)
        db.flush()

        # Seed Inventory record
        inv1 = Inventory(
            id="inv00000-0000-0000-0000-000000000001",
            batch_id=seed_booking.batch_id,
            booking_id=seed_booking.id,
            asset_id=seed_booking.asset_id,
            farmer_id=seed_booking.farmer_id,
            initial_quantity_kg=800.0,
            current_quantity_kg=800.0,
            storage_location="Main Cold Bay A-1",
            received_at=now - datetime.timedelta(days=10),
            expiry_risk_date=now + datetime.timedelta(days=2), # Nearing shelf life!
            status="NEAR_EXPIRY",
            quality_notes="High quality harvest, stored for 10 days at 4C. Color turning bright red."
        )
        db.add(inv1)
        db.flush()

        # Seed Alert for Operator
        alert1 = Alert(
            id="alt00000-0000-0000-0000-000000000001",
            user_id=static_op.id,
            asset_id=inv1.asset_id,
            batch_id=inv1.batch_id,
            inventory_id=inv1.id,
            alert_type="NEAR_EXPIRY_WARNING",
            severity="WARNING",
            message=f"Surplus Alert: Inventory item {inv1.id[:8]} (800.0 kg tomato) nearing shelf-life threshold. Review quality and approve for surplus marketplace.",
            is_read=False
        )
        db.add(alert1)

        # Approved Surplus Listing (Visible to Buyer Demo immediately)
        list_at = now - datetime.timedelta(hours=18)
        exp_at = now + datetime.timedelta(hours=30)
        disc_pct, disc_price = calculate_sliding_discount(
            base_price_per_kg=40.0,
            listed_at=list_at,
            expires_at=exp_at,
            now=now
        )
        listing_approved = BuyerListing(
            id="lst00000-0000-0000-0000-000000000001",
            inventory_id=inv1.id,
            asset_id=inv1.asset_id,
            operator_id=static_op.id,
            crop_code="tomato",
            initial_quantity_kg=400.0,
            available_quantity_kg=400.0,
            base_price_per_kg=40.0,
            current_discount_pct=disc_pct,
            discounted_price_per_kg=disc_price,
            status="APPROVED",
            quality_approved_by=static_op.id,
            quality_approved_at=list_at,
            quality_grade="GRADE_A",
            listed_at=list_at,
            expires_at=exp_at,
            notes="Hydro-cooled farm tomatoes, visually inspected and certified intact."
        )
        db.add(listing_approved)

        # Inventory & Approved Surplus Listing for Onion (Supports Bulk Buyer & Combined Needs Presets)
        inv_onion = Inventory(
            id="inv00000-0000-0000-0000-000000000002",
            batch_id="b0000000-0000-0000-0000-000000000005",
            booking_id=seed_booking.id,
            asset_id="a1000000-0000-0000-0000-000000000002", # Godavari Cold Vault
            farmer_id=farmer2.id,
            initial_quantity_kg=1200.0,
            current_quantity_kg=1200.0,
            storage_location="Chamber B-3",
            received_at=now - datetime.timedelta(days=15),
            expiry_risk_date=now + datetime.timedelta(days=3),
            status="NEAR_EXPIRY",
            quality_notes="Rabi cured red storage onions, Grade A sorted."
        )
        db.add(inv_onion)
        db.flush()

        onion_list_at = now - datetime.timedelta(hours=14)
        onion_exp_at = now + datetime.timedelta(hours=34)
        onion_disc_pct, onion_disc_price = calculate_sliding_discount(
            base_price_per_kg=35.0,
            listed_at=onion_list_at,
            expires_at=onion_exp_at,
            now=now
        )
        listing_onion = BuyerListing(
            id="lst00000-0000-0000-0000-000000000003",
            inventory_id=inv_onion.id,
            asset_id=inv_onion.asset_id,
            operator_id=static_op.id,
            crop_code="onion",
            initial_quantity_kg=800.0,
            available_quantity_kg=800.0,
            base_price_per_kg=35.0,
            current_discount_pct=onion_disc_pct,
            discounted_price_per_kg=onion_disc_price,
            status="APPROVED",
            quality_approved_by=static_op.id,
            quality_approved_at=onion_list_at,
            quality_grade="GRADE_A",
            listed_at=onion_list_at,
            expires_at=onion_exp_at,
            notes="Cured Rabi red onions, Grade A certified for commercial processing."
        )
        db.add(listing_onion)

        # Inventory & Approved Surplus Listing for Pomegranate (Supports Bulk Buyer Preset)
        inv_pom = Inventory(
            id="inv00000-0000-0000-0000-000000000003",
            batch_id="b0000000-0000-0000-0000-000000000009",
            booking_id=seed_booking.id,
            asset_id="a1000000-0000-0000-0000-000000000001", # Nashik Agro Warehouse A
            farmer_id=farmer4.id,
            initial_quantity_kg=700.0,
            current_quantity_kg=700.0,
            storage_location="Chamber C-1",
            received_at=now - datetime.timedelta(days=12),
            expiry_risk_date=now + datetime.timedelta(days=2),
            status="NEAR_EXPIRY",
            quality_notes="Bhagwa variety pomegranates, pre-cooled at 6C."
        )
        db.add(inv_pom)
        db.flush()

        pom_list_at = now - datetime.timedelta(hours=10)
        pom_exp_at = now + datetime.timedelta(hours=38)
        pom_disc_pct, pom_disc_price = calculate_sliding_discount(
            base_price_per_kg=80.0,
            listed_at=pom_list_at,
            expires_at=pom_exp_at,
            now=now
        )
        listing_pom = BuyerListing(
            id="lst00000-0000-0000-0000-000000000004",
            inventory_id=inv_pom.id,
            asset_id=inv_pom.asset_id,
            operator_id=static_op.id,
            crop_code="pomegranate",
            initial_quantity_kg=600.0,
            available_quantity_kg=600.0,
            base_price_per_kg=80.0,
            current_discount_pct=pom_disc_pct,
            discounted_price_per_kg=pom_disc_price,
            status="APPROVED",
            quality_approved_by=static_op.id,
            quality_approved_at=pom_list_at,
            quality_grade="GRADE_A",
            listed_at=pom_list_at,
            expires_at=pom_exp_at,
            notes="Bhagwa export surplus, certified fresh with verified brix sugar levels."
        )
        db.add(listing_pom)

        # Pending Approval Listing (To demonstrate operator quality check on stage)
        listing_pending = BuyerListing(
            id="lst00000-0000-0000-0000-000000000002",
            inventory_id=inv1.id,
            asset_id=inv1.asset_id,
            operator_id=static_op.id,
            crop_code="tomato",
            initial_quantity_kg=250.0,
            available_quantity_kg=250.0,
            base_price_per_kg=35.0,
            current_discount_pct=10.0,
            discounted_price_per_kg=31.5,
            status="PENDING_APPROVAL",
            quality_approved_by=None,
            quality_approved_at=None,
            quality_grade="GRADE_B",
            listed_at=now,
            expires_at=now + datetime.timedelta(hours=48),
            notes="Pending physical firmness and brix inspection before release."
        )
        db.add(listing_pending)

        # 6. DEMAND FORECAST SEEDING
        for est in DEFAULT_SEASONAL_ESTIMATES:
            db.add(DemandForecast(
                crop_code=est["crop_code"],
                district=est["district"],
                horizon_days=est["horizon_days"],
                estimated_demand_kg=est["estimated_demand_kg"],
                price_trend=est["price_trend"],
                expected_price_inr_kg=est["expected_price_inr_kg"],
                forecast_source="SEASONAL_RULE_BASED",
                notes=est["notes"]
            ))

        db.commit()
        print("Demo data seeded successfully with deterministic Phase 1 & Phase 2 records.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    seed_demo_data()
