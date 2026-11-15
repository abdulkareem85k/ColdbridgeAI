# Import all the models, so that Base has them before being
# imported by Alembic or the app runtime.
from app.models.base_class import Base
from app.models.user import User, FarmerProfile, OperatorProfile, BuyerProfile
from app.models.asset import ColdAsset, StaticAssetDetail, MobileAssetDetail, AssetAvailability
from app.models.produce import ProduceBatch, SpoilageAssessment
from app.models.matching import MatchingRequest, Bid
from app.models.booking import Booking
from app.models.route import RouteCache
from app.models.audit import AuditLog
from app.models.inventory import Inventory, Alert
from app.models.marketplace import BuyerListing, PurchaseOrder
from app.models.forecast import DemandForecast

__all__ = [
    "Base",
    "User",
    "FarmerProfile",
    "OperatorProfile",
    "BuyerProfile",
    "ColdAsset",
    "StaticAssetDetail",
    "MobileAssetDetail",
    "AssetAvailability",
    "ProduceBatch",
    "SpoilageAssessment",
    "MatchingRequest",
    "Bid",
    "Booking",
    "RouteCache",
    "AuditLog",
    "Inventory",
    "Alert",
    "BuyerListing",
    "PurchaseOrder",
    "DemandForecast"
]
