"""
ColdBridge AI - Matching Engine Service (M5)

Coordinates cross-asset matching, road distance calculation via OpenStreetMap/OSRM,
eligibility filtering, reverse-auction scoring, and 3-way baseline comparison
(Nearest vs Cheapest vs ColdBridge).
"""

import datetime
from datetime import timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.produce import ProduceBatch, SpoilageAssessment
from app.models.asset import ColdAsset
from app.models.matching import MatchingRequest, Bid
from app.services.maps_service import compute_route
from app.services.sri_engine import calculate_sri
from app.services.eligibility import filter_eligible_assets
from app.services.auction_scoring import score_and_rank_offers, MATCHING_CONFIG


def run_cross_asset_matching(
    db: Session,
    request: MatchingRequest,
    solar_overrides: Dict[str, float] = None,
    now: datetime.datetime = None,
    persist_bids: bool = True
) -> Dict[str, Any]:
    """
    Executes cross-asset matching for a MatchingRequest.
    Returns:
        - ranked_offers: scored and ranked eligible bids
        - baselines: { "coldbridge_pick", "nearest_pick", "cheapest_pick", "explanation" }
        - excluded_assets: list of excluded candidate assets with reasons
        - sri_assessment: SRI band, score, and reasons for the batch
    """
    if now is None:
        now = datetime.datetime.now(timezone.utc)

    batch = request.batch
    if not batch:
        batch = db.query(ProduceBatch).filter_by(id=request.batch_id).first()
    if not batch:
        raise ValueError(f"Produce batch {request.batch_id} not found")

    # 1. Determine SRI for the batch
    sri_assessment = db.query(SpoilageAssessment).filter_by(batch_id=batch.id).order_by(SpoilageAssessment.created_at.desc()).first()
    if not sri_assessment:
        harvest_at = batch.harvest_at
        if harvest_at.tzinfo is None:
            harvest_at = harvest_at.replace(tzinfo=timezone.utc)
        hours_since = max(0.0, (now - harvest_at).total_seconds() / 3600.0)
        sri_res = calculate_sri(
            crop_code=batch.crop_code,
            hours_since_harvest=hours_since,
            ambient_temp_c=batch.ambient_temp_c
        )
        sri_band = sri_res.get("risk_band") or sri_res.get("risk_category", "LOW")
        sri_data = {
            "sri_score": sri_res.get("score"),
            "risk_band": sri_band,
            "reasons": sri_res.get("reasons", []),
            "disclaimer": sri_res.get("disclaimer")
        }
    else:
        sri_band = sri_assessment.risk_band
        sri_data = {
            "sri_score": sri_assessment.sri_score,
            "risk_band": sri_assessment.risk_band,
            "reasons": sri_assessment.reasons or []
        }

    # Check if request is already allocated / matched with an accepted bid
    accepted_bid = None
    if request.bids:
        for b in request.bids:
            if b.is_accepted:
                accepted_bid = b
                break

    if (request.status in ["ALLOCATED", "MATCHED"] or accepted_bid) and accepted_bid:
        asset = accepted_bid.asset or db.query(ColdAsset).filter_by(id=accepted_bid.asset_id).first()
        batch_lat = batch.latitude or 19.9975
        batch_lng = batch.longitude or 73.7898
        asset_lat = asset.latitude if asset else batch_lat
        asset_lng = asset.longitude if asset else batch_lng
        route_info = compute_route(
            origin=(batch_lat, batch_lng),
            destination=(asset_lat, asset_lng),
            db=db
        ) if asset else {"distance_km": 0.0, "route_source": "STORED", "encoded_polyline": None}

        accepted_offer = {
            "bid_id": accepted_bid.id,
            "asset_id": asset.id if asset else accepted_bid.asset_id,
            "asset_name": asset.name if asset else "Allocated Asset",
            "asset_type": asset.asset_type if asset else "STATIC",
            "rank": 1,
            "is_winner": True,
            "score": float(accepted_bid.score if accepted_bid.score is not None else 1.0),
            "unrounded_score": float(accepted_bid.score if accepted_bid.score is not None else 1.0),
            "price_total": float(accepted_bid.price_total),
            "distance_km": float(route_info["distance_km"]),
            "eta_minutes": float(accepted_bid.eta_minutes if accepted_bid.eta_minutes is not None else 0.0),
            "available_capacity_kg": float(asset.available_capacity_kg if asset else 0.0),
            "effective_available_kg": float(accepted_bid.offered_capacity_kg),
            "solar_reliability": 1.0,
            "route_source": route_info.get("route_source", "STORED"),
            "encoded_polyline": route_info.get("encoded_polyline"),
            "geometry": route_info.get("encoded_polyline"),
            "note": accepted_bid.note or "",
            "data_source": accepted_bid.data_source or "SIMULATED",
            "is_persisted": True,
            "latitude": asset_lat,
            "longitude": asset_lng,
            "reasons": ["Accepted allocated offer."],
            "components": {}
        }
        pick_dict = {
            "bid_id": accepted_bid.id,
            "asset_id": accepted_offer["asset_id"],
            "asset_name": accepted_offer["asset_name"],
            "asset_type": accepted_offer["asset_type"],
            "score": accepted_offer["score"],
            "price_total": accepted_offer["price_total"],
            "distance_km": accepted_offer["distance_km"],
            "eta_minutes": accepted_offer["eta_minutes"],
            "data_source": accepted_offer["data_source"]
        }
        return {
            "request_id": request.id,
            "batch_id": batch.id,
            "requested_quantity_kg": request.requested_quantity_kg,
            "sri_assessment": sri_data,
            "ranked_offers": [accepted_offer],
            "baselines": {
                "coldbridge_pick": pick_dict,
                "nearest_pick": pick_dict,
                "cheapest_pick": pick_dict,
                "explanation": f"Allocated offer accepted for {accepted_offer['asset_name']}."
            },
            "excluded_assets": [],
            "matching_config": MATCHING_CONFIG
        }

    # 2. Retrieve all active assets
    all_assets = db.query(ColdAsset).filter_by(is_active=True).all()

    # 3. Calculate distances and routes from batch to each asset
    distances_km = {}
    etas_minutes = {}
    route_sources = {}
    route_geometries = {}

    batch_lat = batch.latitude or 19.9975
    batch_lng = batch.longitude or 73.7898

    for asset in all_assets:
        route_info = compute_route(
            origin=(batch_lat, batch_lng),
            destination=(asset.latitude, asset.longitude),
            db=db
        )
        distances_km[asset.id] = route_info["distance_km"]
        # Add slight dispatch handling buffer (10 mins for van dispatch, 20 mins for static room receiving)
        buffer = 10.0 if asset.asset_type == "MOBILE" else 20.0
        etas_minutes[asset.id] = round(route_info["duration_minutes"] + buffer, 1)
        route_sources[asset.id] = route_info["route_source"]
        route_geometries[asset.id] = route_info.get("encoded_polyline")

    # 4. Run Eligibility Filter
    eligible_entries, excluded_entries = filter_eligible_assets(
        assets=all_assets,
        crop_code=batch.crop_code,
        requested_quantity_kg=request.requested_quantity_kg,
        distances_km=distances_km,
        solar_overrides=solar_overrides,
        now=now
    )

    # 5. Build offer candidates (using existing non-expired bids if recorded, or generating realistic simulated bids)
    existing_bids_by_asset = {}
    if request.bids:
        for b in request.bids:
            is_time_expired = False
            if b.valid_until:
                v_until = b.valid_until.replace(tzinfo=timezone.utc) if b.valid_until.tzinfo is None else b.valid_until
                if v_until < now:
                    is_time_expired = True
                    if persist_bids:
                        b.is_expired = True

            if not b.is_expired and not is_time_expired:
                existing_bids_by_asset[b.asset_id] = b

    raw_offers = []
    for entry in eligible_entries:
        asset = entry["asset"]
        meta = entry["metadata"]
        existing_bid = existing_bids_by_asset.get(asset.id)

        if existing_bid:
            price_total = existing_bid.price_total
            eta_minutes = existing_bid.eta_minutes
            offered_cap = existing_bid.offered_capacity_kg
            note = existing_bid.note or ""
            data_source = existing_bid.data_source or "SIMULATED"
            bid_id = existing_bid.id
            is_persisted = True
        else:
            # Generate prototype bid
            days_est = 3.0
            storage_cost = asset.price_per_kg_per_day * request.requested_quantity_kg * days_est
            transport_cost = distances_km[asset.id] * (15.0 if asset.asset_type == "MOBILE" else 8.0)
            price_total = round(storage_cost + transport_cost, 2)
            eta_minutes = etas_minutes[asset.id]
            offered_cap = meta["effective_capacity_kg"]
            note = f"Automatic simulated offer for {asset.name}"
            data_source = "SIMULATED"

            if persist_bids:
                new_bid = Bid(
                    request_id=request.id,
                    asset_id=asset.id,
                    offered_capacity_kg=float(offered_cap),
                    price_total=float(price_total),
                    eta_minutes=float(eta_minutes),
                    valid_until=now + datetime.timedelta(hours=2),
                    note=note,
                    data_source="SIMULATED",
                    is_accepted=False,
                    is_expired=False
                )
                db.add(new_bid)
                db.flush()
                bid_id = new_bid.id
                is_persisted = True
                existing_bids_by_asset[asset.id] = new_bid
            else:
                bid_id = f"preview-{asset.id[:8]}"
                is_persisted = False

        raw_offers.append({
            "bid_id": bid_id,
            "asset_id": asset.id,
            "asset_name": asset.name,
            "asset_type": asset.asset_type,
            "price_total": float(price_total),
            "distance_km": float(distances_km[asset.id]),
            "eta_minutes": float(eta_minutes),
            "available_capacity_kg": float(asset.available_capacity_kg),
            "effective_available_kg": float(meta["effective_capacity_kg"]),
            "solar_reliability": float(meta.get("solar_reliability", 1.0)),
            "route_source": route_sources[asset.id],
            "encoded_polyline": route_geometries[asset.id],
            "geometry": route_geometries[asset.id],
            "note": note,
            "data_source": data_source,
            "is_persisted": is_persisted,
            "latitude": asset.latitude,
            "longitude": asset.longitude
        })

    # 6. Score and rank eligible offers
    ranked_offers = score_and_rank_offers(
        offers=raw_offers,
        requested_kg=request.requested_quantity_kg,
        sri_band=sri_band
    )

    # If persisted, update bid score on DB records
    if persist_bids:
        for offer in ranked_offers:
            if offer.get("is_persisted") and "score" in offer:
                b_record = db.query(Bid).filter_by(id=offer["bid_id"]).first()
                if b_record:
                    b_record.score = offer["score"]

    # 7. Baseline Comparisons (Nearest vs Cheapest vs ColdBridge)
    baselines = compute_baselines(ranked_offers, sri_band)

    # Format excluded assets for response
    excluded_summary = []
    for exc in excluded_entries:
        excluded_summary.append({
            "asset_id": exc["asset"].id,
            "asset_name": exc["asset"].name,
            "asset_type": exc["asset"].asset_type,
            "reason": exc["reason"],
            "metadata": exc["metadata"]
        })

    return {
        "request_id": request.id,
        "batch_id": batch.id,
        "requested_quantity_kg": request.requested_quantity_kg,
        "sri_assessment": sri_data,
        "ranked_offers": ranked_offers,
        "baselines": baselines,
        "excluded_assets": excluded_summary,
        "matching_config": MATCHING_CONFIG
    }


def compute_baselines(ranked_offers: List[Dict[str, Any]], sri_band: str) -> Dict[str, Any]:
    """
    Computes three picks over the eligible offers:
    1. ColdBridge Pick (winner of multi-criteria reverse auction)
    2. Nearest Eligible (lowest distance_km)
    3. Lowest Price Eligible (lowest price_total)
    And generates explanation of differences.
    """
    if not ranked_offers:
        return {
            "coldbridge_pick": None,
            "nearest_pick": None,
            "cheapest_pick": None,
            "explanation": "No eligible offers available to compare."
        }

    coldbridge_pick = ranked_offers[0]
    nearest_pick = min(ranked_offers, key=lambda x: (x["distance_km"], x["price_total"]))
    cheapest_pick = min(ranked_offers, key=lambda x: (x["price_total"], x["distance_km"]))

    # Build comparison explanation
    exp_parts = []
    if coldbridge_pick["bid_id"] == nearest_pick["bid_id"] == cheapest_pick["bid_id"]:
        exp_parts.append(
            f"ColdBridge chose {coldbridge_pick['asset_name']} as it simultaneously satisfies lowest price, nearest distance, and optimal composite score."
        )
    else:
        cb_type = "mobile cooling van" if coldbridge_pick["asset_type"] == "MOBILE" else "static cold room"
        exp_parts.append(
            f"ColdBridge selected {coldbridge_pick['asset_name']} ({cb_type}) with overall score {coldbridge_pick['score']}."
        )
        if coldbridge_pick["bid_id"] != nearest_pick["bid_id"]:
            exp_parts.append(
                f"Nearest option is {nearest_pick['asset_name']} ({nearest_pick['distance_km']:.1f} km vs {coldbridge_pick['distance_km']:.1f} km), but ColdBridge weighed response time and urgency higher."
            )
        if coldbridge_pick["bid_id"] != cheapest_pick["bid_id"]:
            exp_parts.append(
                f"Cheapest option is {cheapest_pick['asset_name']} (₹{cheapest_pick['price_total']:,.2f} vs ₹{coldbridge_pick['price_total']:,.2f}), but ColdBridge avoided its longer transit distance and delay."
            )

    return {
        "coldbridge_pick": {
            "bid_id": coldbridge_pick["bid_id"],
            "asset_id": coldbridge_pick["asset_id"],
            "asset_name": coldbridge_pick["asset_name"],
            "asset_type": coldbridge_pick["asset_type"],
            "score": coldbridge_pick["score"],
            "price_total": coldbridge_pick["price_total"],
            "distance_km": coldbridge_pick["distance_km"],
            "eta_minutes": coldbridge_pick["eta_minutes"],
            "data_source": coldbridge_pick.get("data_source", "SIMULATED")
        },
        "nearest_pick": {
            "bid_id": nearest_pick["bid_id"],
            "asset_id": nearest_pick["asset_id"],
            "asset_name": nearest_pick["asset_name"],
            "asset_type": nearest_pick["asset_type"],
            "score": nearest_pick["score"],
            "price_total": nearest_pick["price_total"],
            "distance_km": nearest_pick["distance_km"],
            "eta_minutes": nearest_pick["eta_minutes"],
            "data_source": nearest_pick.get("data_source", "SIMULATED")
        },
        "cheapest_pick": {
            "bid_id": cheapest_pick["bid_id"],
            "asset_id": cheapest_pick["asset_id"],
            "asset_name": cheapest_pick["asset_name"],
            "asset_type": cheapest_pick["asset_type"],
            "score": cheapest_pick["score"],
            "price_total": cheapest_pick["price_total"],
            "distance_km": cheapest_pick["distance_km"],
            "eta_minutes": cheapest_pick["eta_minutes"],
            "data_source": cheapest_pick.get("data_source", "SIMULATED")
        },
        "explanation": " ".join(exp_parts)
    }
