"""
ColdBridge AI - Public Cold Storage Directory Seed Script (Part 4)

Seeds 10 real public cold storage facilities located in Nashik and Pune.
These entries are from public directories and are NOT ColdBridge partners.
Idempotent upsert by (name, district). Safe to run multiple times.
"""

import sys
import uuid
import logging
from pathlib import Path
from sqlalchemy.orm import Session

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models.directory import PublicColdStorageListing

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("public_directory_seed")

STANDARD_SOURCE_NOTE = (
    "Public business directory listing, accessed 18 Nov 2026. "
    "Not a ColdBridge partner. Call to confirm before visiting."
)

AARAV_SOURCE_NOTE = (
    STANDARD_SOURCE_NOTE +
    " Directory call line; may not be the facility owner's direct phone number."
)

DIRECTORY_ENTRIES = [
    {
        "name": "Bhandari Cold Storage",
        "district": "Nashik",
        "area": "Kokangaon, Niphad",
        "address": "Gat No. 541, Sakara Road, Kokangaon, Tal. Niphad, Nashik 422209",
        "phone": "9371751606",
        "source_note": STANDARD_SOURCE_NOTE
    },
    {
        "name": "Kshirsagar Cold Storage",
        "district": "Nashik",
        "area": "Kokangaon, Niphad",
        "address": "Gat No. 434/A, A/P Kokangaon, Tal. Niphad, Nashik 422206",
        "phone": "9822327671",
        "source_note": STANDARD_SOURCE_NOTE
    },
    {
        "name": "Vishaka Agri Cold Storage",
        "district": "Nashik",
        "area": "Pimpalgaon Baswant",
        "address": "695/1 and 2, Vani Road, Pimpalgaon Baswant, Nashik 422209",
        "phone": "9637183664",
        "source_note": STANDARD_SOURCE_NOTE
    },
    {
        "name": "Manchanda Cold Storage and Warehouses",
        "district": "Nashik",
        "area": "Janori, Dindori",
        "address": "Sr. No. 603/5-A and 603/4, A/P Janori, Tal. Dindori, Nashik 422002",
        "phone": "9822027877",
        "source_note": STANDARD_SOURCE_NOTE
    },
    {
        "name": "Aarav Agro Industries",
        "district": "Nashik",
        "area": "Ambad MIDC",
        "address": "H-23/1, MIDC, near Unique Cranes, Ambad, Nashik 422010",
        "phone": "9700318318",
        "source_note": AARAV_SOURCE_NOTE
    },
    {
        "name": "Aarya Cold Storage and Exports",
        "district": "Nashik",
        "area": "Kokangaon",
        "address": "Mumbai Agra Road (NH3), Kokangaon, Nashik",
        "phone": None,
        "source_note": STANDARD_SOURCE_NOTE
    },
    {
        "name": "Central Warehousing Corporation (Ambad MIDC)",
        "district": "Nashik",
        "area": "Ambad MIDC",
        "address": "Ambad MIDC, Nashik",
        "phone": None,
        "source_note": STANDARD_SOURCE_NOTE
    },
    {
        "name": "Jai Jinendra Cold Storage Pvt Ltd",
        "district": "Pune",
        "area": "Vadki, Haveli",
        "address": "Gat No. 1194/1195, Pune-Saswad Road, Vadki, Tal. Haveli, Pune 412308",
        "phone": "+918046056365",
        "source_note": STANDARD_SOURCE_NOTE
    },
    {
        "name": "Iceage Cold Storage",
        "district": "Pune",
        "area": "Chakan (Kuruli), Khed",
        "address": "Gat No. 285/3/2, Kuruli, near Dongre Wasti, Pune-Nashik Highway, Chakan, Pune 410501",
        "phone": "+918048970373",
        "source_note": STANDARD_SOURCE_NOTE
    },
    {
        "name": "Shrikrishna Agro Cold Storage",
        "district": "Pune",
        "area": "Kalewadi, Purandar",
        "address": "Gate No. 331, Milkat No. 286, Kalewadi, Hadapsar-Saswad Road, Purandar, Pune 412301",
        "phone": None,
        "source_note": STANDARD_SOURCE_NOTE
    }
]


def seed_public_directory(db: Session) -> dict:
    """
    Idempotent upsert of the 10 public cold storage facilities.
    Returns stats dict: {"inserted": int, "updated": int, "untouched": int, "total": int}
    """
    stats = {"inserted": 0, "updated": 0, "untouched": 0, "total": 0}

    for item in DIRECTORY_ENTRIES:
        existing = (
            db.query(PublicColdStorageListing)
            .filter_by(name=item["name"], district=item["district"])
            .first()
        )

        if not existing:
            # Insert new row: is_partner=False, contact_verified=False, lat/lng/capacity/last_checked=None
            new_listing = PublicColdStorageListing(
                id=f"csl-{uuid.uuid4().hex[:12]}",
                name=item["name"],
                district=item["district"],
                area=item["area"],
                address=item["address"],
                phone=item["phone"],
                source_note=item["source_note"],
                latitude=None,
                longitude=None,
                capacity_mt=None,
                is_partner=False,
                contact_verified=False,
                last_checked_on=None
            )
            db.add(new_listing)
            stats["inserted"] += 1
            logger.info("INSERTED: %s (%s)", item["name"], item["district"])
        else:
            # Upsert rules:
            # 1. Never overwrite contact_verified, last_checked_on, or is_partner
            # 2. Never reset a genuine partner to is_partner=False
            # 3. Never overwrite non-NULL latitude, longitude, or capacity_mt
            # 4. If row has contact_verified=True or is_partner=True, do not overwrite address or phone either
            updated = False

            # Check if address/phone can be updated
            can_update_contact = not (existing.contact_verified or existing.is_partner)

            if can_update_contact:
                if existing.address != item["address"]:
                    existing.address = item["address"]
                    updated = True
                if existing.phone != item["phone"]:
                    existing.phone = item["phone"]
                    updated = True

            if existing.area != item["area"]:
                existing.area = item["area"]
                updated = True
            if existing.source_note != item["source_note"]:
                existing.source_note = item["source_note"]
                updated = True

            if updated:
                stats["updated"] += 1
                logger.info("UPDATED: %s (%s)", item["name"], item["district"])
            else:
                stats["untouched"] += 1
                logger.info("UNTOUCHED: %s (%s)", item["name"], item["district"])

    db.commit()
    stats["total"] = db.query(PublicColdStorageListing).count()
    logger.info(
        "Directory Seed Complete: inserted=%d, updated=%d, untouched=%d, total=%d",
        stats["inserted"], stats["updated"], stats["untouched"], stats["total"]
    )
    return stats


def main():
    db = SessionLocal()
    try:
        stats = seed_public_directory(db)
        print(f"Public Directory Seed finished: {stats}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
