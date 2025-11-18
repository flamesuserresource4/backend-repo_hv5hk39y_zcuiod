"""
Database Schemas for TooGoodToGo-style MVP (Albania)

Each Pydantic model represents a MongoDB collection (collection name = lowercase class name).
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class Vendor(BaseModel):
    name: str = Field(..., description="Business/Vendor name")
    city: str = Field(..., description="City where the vendor operates")
    address: Optional[str] = Field(None, description="Street address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    cuisine: Optional[str] = Field(None, description="Cuisine type or category")
    image_url: Optional[HttpUrl] = Field(None, description="Logo or image URL")
    active: bool = Field(True, description="Whether vendor is active")


class Offer(BaseModel):
    title: str = Field(..., description="Offer title (e.g., Surprise Bag)")
    description: Optional[str] = Field(None, description="Short description of what's included")
    vendor_name: str = Field(..., description="Name of the vendor offering the bag")
    city: str = Field(..., description="City of pickup")
    address: Optional[str] = Field(None, description="Pickup address")
    cuisine: Optional[str] = Field(None, description="Cuisine or category")
    tags: List[str] = Field(default_factory=list, description="Tags like bakery, vegan, halal")
    original_price: float = Field(..., ge=0, description="Original total value")
    price: float = Field(..., ge=0, description="Discounted price")
    quantity: int = Field(..., ge=0, description="Number of bags available")
    pickup_start: datetime = Field(..., description="Pickup window start (ISO datetime)")
    pickup_end: datetime = Field(..., description="Pickup window end (ISO datetime)")
    image_url: Optional[HttpUrl] = Field(None, description="Offer image")
    active: bool = Field(True, description="If false, offer hidden")


class Reservation(BaseModel):
    offer_id: str = Field(..., description="ID of the offer reserved")
    customer_name: str = Field(..., description="Name of customer picking up")
    customer_phone: str = Field(..., description="Contact phone")
    quantity: int = Field(1, ge=1, description="How many bags reserved")
    status: str = Field("reserved", description="reserved | picked_up | cancelled")
