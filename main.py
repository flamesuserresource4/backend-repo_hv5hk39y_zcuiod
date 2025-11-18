import os
from datetime import datetime
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Vendor, Offer, Reservation

app = FastAPI(title="MbaroMire API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OfferOut(BaseModel):
    id: str
    title: str
    vendor_name: str
    city: str
    price: float
    original_price: float
    quantity: int
    pickup_start: datetime
    pickup_end: datetime
    image_url: Optional[str] = None
    cuisine: Optional[str] = None
    tags: List[str] = []
    address: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "MbaroMire Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["connection_status"] = "Connected"
            response["collections"] = db.list_collection_names()
        else:
            response["database"] = "❌ Not Connected"
    except Exception as e:
        response["database"] = f"⚠️ {str(e)[:80]}"
    return response


# Seed some cities for filtering
CITIES = ["Tirana", "Durrës", "Shkodër", "Vlorë", "Elbasan"]


@app.get("/api/cities")
def get_cities():
    return {"cities": CITIES}


@app.post("/api/vendors")
def create_vendor(vendor: Vendor):
    vendor_id = create_document("vendor", vendor)
    return {"id": vendor_id}


@app.post("/api/offers")
def create_offer(offer: Offer, admin_code: Optional[str] = Query(default=None)):
    required_code = os.getenv("ADMIN_CODE", "admin123")
    if required_code and admin_code != required_code:
        raise HTTPException(status_code=401, detail="Invalid admin code")

    if offer.price > offer.original_price:
        raise HTTPException(status_code=400, detail="Price must be <= original price")

    offer_id = create_document("offer", offer)
    return {"id": offer_id}


@app.get("/api/offers", response_model=List[OfferOut])
def list_offers(
    city: Optional[str] = None,
    cuisine: Optional[str] = None,
    q: Optional[str] = None,
):
    filt = {"active": True, "quantity": {"$gt": 0}}
    if city:
        filt["city"] = city
    if cuisine:
        filt["cuisine"] = cuisine
    if q:
        filt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"vendor_name": {"$regex": q, "$options": "i"}},
            {"tags": {"$elemMatch": {"$regex": q, "$options": "i"}}},
        ]

    docs = get_documents("offer", filt, limit=100)
    result = []
    for d in docs:
        result.append(
            OfferOut(
                id=str(d.get("_id")),
                title=d.get("title"),
                vendor_name=d.get("vendor_name"),
                city=d.get("city"),
                price=d.get("price"),
                original_price=d.get("original_price"),
                quantity=d.get("quantity"),
                pickup_start=d.get("pickup_start"),
                pickup_end=d.get("pickup_end"),
                image_url=d.get("image_url"),
                cuisine=d.get("cuisine"),
                tags=d.get("tags", []),
                address=d.get("address"),
            )
        )
    return result


@app.get("/api/offers/{offer_id}")
def get_offer(offer_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    doc = db["offer"].find_one({"_id": ObjectId(offer_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Offer not found")
    doc["id"] = str(doc["_id"])  
    doc.pop("_id", None)
    return doc


class ReservationIn(BaseModel):
    offer_id: str
    customer_name: str
    customer_phone: str
    quantity: int = 1


@app.post("/api/reservations")
def reserve(res: ReservationIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    offer = db["offer"].find_one({"_id": ObjectId(res.offer_id)})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.get("quantity", 0) < res.quantity:
        raise HTTPException(status_code=400, detail="Not enough quantity")

    reservation = Reservation(
        offer_id=res.offer_id,
        customer_name=res.customer_name,
        customer_phone=res.customer_phone,
        quantity=res.quantity,
        status="reserved",
    )
    reservation_id = create_document("reservation", reservation)

    db["offer"].update_one(
        {"_id": ObjectId(res.offer_id)},
        {"$inc": {"quantity": -res.quantity}, "$set": {"updated_at": datetime.utcnow()}},
    )

    return {"id": reservation_id, "message": "Reserved"}


@app.get("/schema")
def get_schema():
    return {
        "vendor": Vendor.model_json_schema(),
        "offer": Offer.model_json_schema(),
        "reservation": Reservation.model_json_schema(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
