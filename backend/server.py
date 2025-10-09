from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Crane Orders API", description="Data entry system for crane orders")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class CraneOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    added_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    customer_name: str
    phone: str
    order_type: str  # "cash" or "company"
    
    # Cash order fields
    cash_trip_from: Optional[str] = None
    cash_trip_to: Optional[str] = None
    care_off: Optional[str] = None
    care_off_amount: Optional[float] = None
    cash_vehicle_details: Optional[str] = None
    cash_driver_details: Optional[str] = None
    cash_vehicle_name: Optional[str] = None
    cash_vehicle_number: Optional[str] = None
    cash_service_type: Optional[str] = None
    amount_received: Optional[float] = None
    advance_amount: Optional[float] = None
    cash_kms_travelled: Optional[float] = None
    cash_toll: Optional[float] = None
    diesel: Optional[str] = None
    cash_diesel: Optional[float] = None
    cash_diesel_refill_location: Optional[str] = None
    
    # Company order fields
    name_of_firm: Optional[str] = None
    company_name: Optional[str] = None
    case_id_file_number: Optional[str] = None
    company_vehicle_name: Optional[str] = None
    company_vehicle_number: Optional[str] = None
    company_service_type: Optional[str] = None
    company_vehicle_details: Optional[str] = None
    company_driver_details: Optional[str] = None
    company_trip_from: Optional[str] = None
    company_trip_to: Optional[str] = None
    reach_time: Optional[datetime] = None
    drop_time: Optional[datetime] = None
    company_kms_travelled: Optional[float] = None
    company_toll: Optional[float] = None
    diesel_name: Optional[str] = None
    company_diesel: Optional[float] = None
    company_diesel_refill_location: Optional[str] = None

class CraneOrderCreate(BaseModel):
    customer_name: str
    phone: str
    order_type: str  # "cash" or "company"
    date_time: Optional[datetime] = None
    
    # Cash order fields
    cash_trip_from: Optional[str] = None
    cash_trip_to: Optional[str] = None
    care_off: Optional[str] = None
    care_off_amount: Optional[float] = None
    cash_vehicle_details: Optional[str] = None
    cash_driver_details: Optional[str] = None
    cash_vehicle_name: Optional[str] = None
    cash_vehicle_number: Optional[str] = None
    cash_service_type: Optional[str] = None
    amount_received: Optional[float] = None
    advance_amount: Optional[float] = None
    cash_kms_travelled: Optional[float] = None
    cash_toll: Optional[float] = None
    diesel: Optional[str] = None
    cash_diesel: Optional[float] = None
    cash_diesel_refill_location: Optional[str] = None
    
    # Company order fields
    name_of_firm: Optional[str] = None
    company_name: Optional[str] = None
    case_id_file_number: Optional[str] = None
    company_vehicle_name: Optional[str] = None
    company_vehicle_number: Optional[str] = None
    company_service_type: Optional[str] = None
    company_vehicle_details: Optional[str] = None
    company_driver_details: Optional[str] = None
    company_trip_from: Optional[str] = None
    company_trip_to: Optional[str] = None
    reach_time: Optional[datetime] = None
    drop_time: Optional[datetime] = None
    company_kms_travelled: Optional[float] = None
    company_toll: Optional[float] = None
    diesel_name: Optional[str] = None
    company_diesel: Optional[float] = None
    company_diesel_refill_location: Optional[str] = None

class CraneOrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    order_type: Optional[str] = None
    date_time: Optional[datetime] = None
    
    # Cash order fields
    cash_trip_from: Optional[str] = None
    cash_trip_to: Optional[str] = None
    care_off: Optional[str] = None
    care_off_amount: Optional[float] = None
    cash_vehicle_details: Optional[str] = None
    cash_driver_details: Optional[str] = None
    cash_vehicle_name: Optional[str] = None
    cash_vehicle_number: Optional[str] = None
    cash_service_type: Optional[str] = None
    amount_received: Optional[float] = None
    advance_amount: Optional[float] = None
    cash_kms_travelled: Optional[float] = None
    cash_toll: Optional[float] = None
    diesel: Optional[str] = None
    cash_diesel: Optional[float] = None
    cash_diesel_refill_location: Optional[str] = None
    
    # Company order fields
    name_of_firm: Optional[str] = None
    company_name: Optional[str] = None
    case_id_file_number: Optional[str] = None
    company_vehicle_name: Optional[str] = None
    company_vehicle_number: Optional[str] = None
    company_service_type: Optional[str] = None
    company_vehicle_details: Optional[str] = None
    company_driver_details: Optional[str] = None
    company_trip_from: Optional[str] = None
    company_trip_to: Optional[str] = None
    reach_time: Optional[datetime] = None
    drop_time: Optional[datetime] = None
    company_kms_travelled: Optional[float] = None
    company_toll: Optional[float] = None
    diesel_name: Optional[str] = None
    company_diesel: Optional[float] = None
    company_diesel_refill_location: Optional[str] = None

# Helper functions for MongoDB serialization
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    doc = dict(data)
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc

def parse_from_mongo(item):
    """Convert ISO strings back to datetime objects from MongoDB"""
    if not item:
        return item
    
    datetime_fields = ['added_time', 'date_time', 'reach_time', 'drop_time']
    for field in datetime_fields:
        if field in item and isinstance(item[field], str):
            try:
                item[field] = datetime.fromisoformat(item[field])
            except ValueError:
                continue
    return item

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Crane Orders Data Entry System"}

@api_router.post("/orders", response_model=CraneOrder)
async def create_order(input: CraneOrderCreate):
    """Create a new crane order"""
    order_dict = input.model_dump(exclude_unset=True)
    
    # Set default datetime if not provided
    if not order_dict.get('date_time'):
        order_dict['date_time'] = datetime.now(timezone.utc)
    
    order_obj = CraneOrder(**order_dict)
    
    # Convert to dict and serialize datetime fields for MongoDB
    doc = prepare_for_mongo(order_obj.model_dump())
    
    try:
        result = await db.crane_orders.insert_one(doc)
        return order_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@api_router.get("/orders", response_model=List[CraneOrder])
async def get_orders(
    order_type: Optional[str] = Query(None, description="Filter by order type (cash/company)"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    phone: Optional[str] = Query(None, description="Filter by phone number"),
    limit: int = Query(100, ge=1, le=1000, description="Number of orders to return"),
    skip: int = Query(0, ge=0, description="Number of orders to skip")
):
    """Get all crane orders with optional filtering"""
    query = {}
    
    # Build query filters
    if order_type:
        query["order_type"] = order_type
    if customer_name:
        query["customer_name"] = {"$regex": customer_name, "$options": "i"}
    if phone:
        query["phone"] = {"$regex": phone, "$options": "i"}
    
    try:
        # Exclude MongoDB's _id field from results
        orders = await db.crane_orders.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
        
        # Parse datetime fields from MongoDB
        parsed_orders = [parse_from_mongo(order) for order in orders]
        
        return parsed_orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")

@api_router.get("/orders/{order_id}", response_model=CraneOrder)
async def get_order(order_id: str):
    """Get a specific crane order by ID"""
    try:
        order = await db.crane_orders.find_one({"id": order_id}, {"_id": 0})
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return parse_from_mongo(order)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error fetching order: {str(e)}")

@api_router.put("/orders/{order_id}", response_model=CraneOrder)
async def update_order(order_id: str, update_data: CraneOrderUpdate):
    """Update a specific crane order"""
    try:
        # Check if order exists
        existing_order = await db.crane_orders.find_one({"id": order_id}, {"_id": 0})
        if not existing_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Prepare update data
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        if update_dict:
            # Serialize datetime fields
            prepared_update = prepare_for_mongo(update_dict)
            
            # Update the order
            result = await db.crane_orders.update_one(
                {"id": order_id},
                {"$set": prepared_update}
            )
            
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Order not found")
        
        # Fetch and return updated order
        updated_order = await db.crane_orders.find_one({"id": order_id}, {"_id": 0})
        return parse_from_mongo(updated_order)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error updating order: {str(e)}")

@api_router.delete("/orders/{order_id}")
async def delete_order(order_id: str):
    """Delete a specific crane order"""
    try:
        result = await db.crane_orders.delete_one({"id": order_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {"message": "Order deleted successfully"}
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error deleting order: {str(e)}")

@api_router.get("/orders/stats/summary")
async def get_orders_summary():
    """Get summary statistics of orders"""
    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$order_type",
                    "count": {"$sum": 1},
                    "total_amount": {
                        "$sum": {
                            "$cond": {
                                "if": {"$eq": ["$order_type", "cash"]},
                                "then": "$amount_received",
                                "else": 0
                            }
                        }
                    }
                }
            }
        ]
        
        stats = await db.crane_orders.aggregate(pipeline).to_list(None)
        
        # Calculate total orders
        total_orders = await db.crane_orders.count_documents({})
        
        return {
            "total_orders": total_orders,
            "by_type": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
