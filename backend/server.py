from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from enum import Enum
import bcrypt
from fastapi.responses import StreamingResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import gspread
from google.oauth2.service_account import Credentials
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security configurations
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Kawale Cranes API", description="Data entry system for Kawale Cranes orders with authentication")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# User Roles Enum
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DATA_ENTRY = "data_entry"

# Define Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    action: str  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    resource_type: str  # USER, ORDER
    resource_id: Optional[str] = None
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class CraneOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    added_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    unique_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    customer_name: str
    phone: str
    order_type: str  # "cash" or "company"
    
    # Audit fields
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    # Incentive fields (admin only)
    incentive_amount: Optional[float] = None
    incentive_reason: Optional[str] = None
    incentive_added_by: Optional[str] = None
    incentive_added_at: Optional[datetime] = None
    
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
    cash_driver_name: Optional[str] = None
    cash_towing_vehicle: Optional[str] = None
    
    # Company order fields
    name_of_firm: Optional[str] = None
    company_name: Optional[str] = None  # Mandatory via endpoint validation
    case_id_file_number: Optional[str] = None
    company_vehicle_name: Optional[str] = None
    company_vehicle_number: Optional[str] = None
    company_service_type: Optional[str] = None  # Mandatory via endpoint validation
    company_vehicle_details: Optional[str] = None
    company_driver_details: Optional[str] = None  # Mandatory via endpoint validation (Driver)
    company_trip_from: Optional[str] = None
    company_trip_to: Optional[str] = None
    reach_time: Optional[datetime] = None
    drop_time: Optional[datetime] = None
    company_kms_travelled: Optional[float] = None
    company_toll: Optional[float] = None
    diesel_name: Optional[str] = None
    company_diesel: Optional[float] = None
    company_diesel_refill_location: Optional[str] = None
    company_driver_name: Optional[str] = None
    company_towing_vehicle: Optional[str] = None  # Mandatory via endpoint validation (Towing Vehicle)

class CraneOrderCreate(BaseModel):
    customer_name: str
    phone: str
    order_type: str
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
    cash_driver_name: Optional[str] = None
    cash_towing_vehicle: Optional[str] = None
    
    # Company order fields
    name_of_firm: Optional[str] = None
    company_name: Optional[str] = None  # Mandatory via endpoint validation
    case_id_file_number: Optional[str] = None
    company_vehicle_name: Optional[str] = None
    company_vehicle_number: Optional[str] = None
    company_service_type: Optional[str] = None  # Mandatory via endpoint validation
    company_vehicle_details: Optional[str] = None
    company_driver_details: Optional[str] = None  # Mandatory via endpoint validation (Driver)
    company_trip_from: Optional[str] = None
    company_trip_to: Optional[str] = None
    reach_time: Optional[datetime] = None
    drop_time: Optional[datetime] = None
    company_kms_travelled: Optional[float] = None
    company_toll: Optional[float] = None
    diesel_name: Optional[str] = None
    company_diesel: Optional[float] = None
    company_diesel_refill_location: Optional[str] = None
    company_driver_name: Optional[str] = None
    company_towing_vehicle: Optional[str] = None  # Mandatory via endpoint validation (Towing Vehicle)
    
    # Incentive fields (admin only)
    incentive_amount: Optional[float] = None
    incentive_reason: Optional[str] = None
    incentive_added_by: Optional[str] = None
    incentive_added_at: Optional[datetime] = None

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
    cash_driver_name: Optional[str] = None
    cash_towing_vehicle: Optional[str] = None
    
    # Company order fields
    name_of_firm: Optional[str] = None
    company_name: Optional[str] = None  # Mandatory in main model but optional for updates
    case_id_file_number: Optional[str] = None
    company_vehicle_name: Optional[str] = None
    company_vehicle_number: Optional[str] = None
    company_service_type: Optional[str] = None  # Mandatory in main model but optional for updates
    company_vehicle_details: Optional[str] = None
    company_driver_details: Optional[str] = None  # Mandatory in main model but optional for updates
    company_trip_from: Optional[str] = None
    company_trip_to: Optional[str] = None
    reach_time: Optional[datetime] = None
    drop_time: Optional[datetime] = None
    company_kms_travelled: Optional[float] = None
    company_toll: Optional[float] = None
    diesel_name: Optional[str] = None
    company_diesel: Optional[float] = None
    company_diesel_refill_location: Optional[str] = None
    company_driver_name: Optional[str] = None
    company_towing_vehicle: Optional[str] = None  # Mandatory in main model but optional for updates
    
    # Incentive fields (admin only)
    incentive_amount: Optional[float] = None
    incentive_reason: Optional[str] = None
    incentive_added_by: Optional[str] = None
    incentive_added_at: Optional[datetime] = None

class ServiceRate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name_of_firm: str
    company_name: str
    service_type: str
    base_rate: float  # Rate for base distance (up to 40km)
    base_distance_km: float = Field(default=40.0)  # Base distance in km
    rate_per_km_beyond: float  # Rate per km beyond base distance
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CalculatedOrderFinancials(BaseModel):
    """Calculated financial data for an order"""
    base_revenue: float = 0.0  # Revenue from rate calculation
    incentive_amount: float = 0.0  # Incentive paid
    total_revenue: float = 0.0  # base_revenue + incentive_amount
    calculation_details: Optional[str] = None  # Details of how calculation was done

# Helper functions for MongoDB serialization
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    doc = dict(data)
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc

def parse_from_mongo(item):
    """Convert ISO strings back to datetime objects from MongoDB and handle None values"""
    if not item:
        return item
    
    # Convert datetime fields
    datetime_fields = ['added_time', 'date_time', 'reach_time', 'drop_time', 'created_at', 'updated_at', 'last_login', 'timestamp', 'incentive_added_at']
    for field in datetime_fields:
        if field in item and isinstance(item[field], str):
            try:
                item[field] = datetime.fromisoformat(item[field])
            except ValueError:
                continue
    
    # Handle None values in string fields that should be Optional[str] but not None for Pydantic validation
    # Convert None to empty string for optional string fields to avoid Pydantic validation errors
    optional_string_fields = [
        'cash_trip_from', 'cash_trip_to', 'care_off', 'cash_vehicle_details', 'cash_driver_details',
        'cash_vehicle_name', 'cash_vehicle_number', 'cash_service_type', 'diesel', 'cash_diesel_refill_location',
        'cash_driver_name', 'cash_towing_vehicle', 'name_of_firm', 'company_name', 'case_id_file_number',
        'company_vehicle_name', 'company_vehicle_number', 'company_service_type', 'company_vehicle_details',
        'company_driver_details', 'company_trip_from', 'company_trip_to', 'diesel_name',
        'company_diesel_refill_location', 'company_driver_name', 'company_towing_vehicle', 'incentive_reason'
    ]
    
    for field in optional_string_fields:
        if field in item and item[field] is None:
            item[field] = ""  # Convert None to empty string
    
    return item

# Authentication utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_email(email: str):
    user = await db.users.find_one({"email": email}, {"_id": 0})
    return parse_from_mongo(user) if user else None

async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user:
        return False
    
    # Get user with password for authentication
    user_with_password = await db.users.find_one({"email": email})
    if not user_with_password or not verify_password(password, user_with_password["hashed_password"]):
        return False
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(email)
    if user is None:
        raise credentials_exception
    
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user

def require_role(allowed_roles: List[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

async def log_audit(user_id: str, user_email: str, action: str, resource_type: str, 
                   resource_id: str = None, old_data: Dict = None, new_data: Dict = None,
                   ip_address: str = None, user_agent: str = None):
    """Log audit trail"""
    audit_log = AuditLog(
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_data=old_data,
        new_data=new_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    doc = prepare_for_mongo(audit_log.model_dump())
    await db.audit_logs.insert_one(doc)

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Kawale Cranes Data Entry System with Authentication"}

# Authentication endpoints
@api_router.post("/auth/register", response_model=User)
async def register_user(user_data: UserCreate, current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))):
    """Register a new user (Admin and Super Admin only)"""
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        created_by=current_user["id"]
    )
    
    # Store user with hashed password
    user_doc = prepare_for_mongo(user.model_dump())
    user_doc["hashed_password"] = hashed_password
    
    await db.users.insert_one(user_doc)
    
    # Log audit
    await log_audit(
        user_id=current_user["id"],
        user_email=current_user["email"],
        action="CREATE",
        resource_type="USER",
        resource_id=user.id,
        new_data={"email": user.email, "full_name": user.full_name, "role": user.role}
    )
    
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authenticate user and return token"""
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    await db.users.update_one(
        {"email": user["email"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    # Log audit
    await log_audit(
        user_id=user["id"],
        user_email=user["email"],
        action="LOGIN",
        resource_type="USER",
        resource_id=user["id"]
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user)
    }

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return User(**current_user)

@api_router.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (mainly for audit trail)"""
    # Log audit
    await log_audit(
        user_id=current_user["id"],
        user_email=current_user["email"],
        action="LOGOUT",
        resource_type="USER",
        resource_id=current_user["id"]
    )
    
    return {"message": "Logged out successfully"}

# User management endpoints
@api_router.get("/users", response_model=List[User])
async def get_users(
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN])),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all users (Admin and Super Admin only)"""
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).limit(limit).to_list(limit)
    return [User(**parse_from_mongo(user)) for user in users]

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """Update user (Admin and Super Admin only)"""
    # Get existing user
    existing_user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update
    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if update_dict:
        prepared_update = prepare_for_mongo(update_dict)
        
        # Update user
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": prepared_update}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Log audit
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action="UPDATE",
            resource_type="USER",
            resource_id=user_id,
            old_data=existing_user,
            new_data=update_dict
        )
    
    # Return updated user
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    return User(**parse_from_mongo(updated_user))

@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Delete user (Super Admin only)"""
    try:
        # Prevent self-deletion
        if user_id == current_user["id"]:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Get user for audit log
        existing_user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        result = await db.users.delete_one({"id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Log audit
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action="DELETE",
            resource_type="USER",
            resource_id=user_id,
            old_data=existing_user
        )
        
        return {"message": "User deleted successfully"}
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

# Order endpoints (with authentication and audit)
@api_router.post("/orders", response_model=CraneOrder)
async def create_order(
    input: CraneOrderCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new crane order"""
    order_dict = input.model_dump(exclude_unset=True)
    
    # Set default datetime if not provided
    if not order_dict.get('date_time'):
        order_dict['date_time'] = datetime.now(timezone.utc)
    
    # Add audit fields
    order_dict['created_by'] = current_user["id"]
    
    order_obj = CraneOrder(**order_dict)
    
    # Validate mandatory fields for company orders
    if order_obj.order_type == "company":
        missing_fields = []
        
        if not order_obj.company_name or order_obj.company_name.strip() == "":
            missing_fields.append("Company Name")
        
        if not order_obj.company_service_type or order_obj.company_service_type.strip() == "":
            missing_fields.append("Service Type")
        
        if not order_obj.company_driver_details or order_obj.company_driver_details.strip() == "":
            missing_fields.append("Driver")
        
        if not order_obj.company_towing_vehicle or order_obj.company_towing_vehicle.strip() == "":
            missing_fields.append("Towing Vehicle")
        
        if missing_fields:
            field_list = ", ".join(missing_fields)
            raise HTTPException(
                status_code=422, 
                detail=f"The following fields are required for company orders: {field_list}"
            )
    
    # Convert to dict and serialize datetime fields for MongoDB
    doc = prepare_for_mongo(order_obj.model_dump())
    
    try:
        result = await db.crane_orders.insert_one(doc)
        
        # Log audit
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action="CREATE",
            resource_type="ORDER",
            resource_id=order_obj.id,
            new_data=order_dict
        )
        
        return order_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@api_router.get("/orders", response_model=List[CraneOrder])
async def get_orders(
    current_user: dict = Depends(get_current_user),
    order_type: Optional[str] = Query(None, description="Filter by order type (cash/company)"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    phone: Optional[str] = Query(None, description="Filter by phone number"),
    limit: int = Query(100, ge=1, le=1000, description="Number of orders to return"),
    skip: int = Query(0, ge=0, description="Number of orders to skip")
):
    """Get all crane orders"""
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
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
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
async def update_order(
    order_id: str,
    update_data: CraneOrderUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a specific crane order"""
    try:
        # Check if order exists
        existing_order = await db.crane_orders.find_one({"id": order_id}, {"_id": 0})
        if not existing_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Prepare update data
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        if update_dict:
            # Create a combined dict of existing order + updates for validation
            combined_data = {**existing_order, **update_dict}
            
            # Validate mandatory fields for company orders
            if combined_data.get("order_type") == "company":
                missing_fields = []
                
                company_name = combined_data.get("company_name", "")
                if not company_name or (isinstance(company_name, str) and company_name.strip() == ""):
                    missing_fields.append("Company Name")
                
                company_service_type = combined_data.get("company_service_type", "")
                if not company_service_type or (isinstance(company_service_type, str) and company_service_type.strip() == ""):
                    missing_fields.append("Service Type")
                
                company_driver_details = combined_data.get("company_driver_details", "")
                if not company_driver_details or (isinstance(company_driver_details, str) and company_driver_details.strip() == ""):
                    missing_fields.append("Driver")
                
                company_towing_vehicle = combined_data.get("company_towing_vehicle", "")
                if not company_towing_vehicle or (isinstance(company_towing_vehicle, str) and company_towing_vehicle.strip() == ""):
                    missing_fields.append("Towing Vehicle")
                
                if missing_fields:
                    field_list = ", ".join(missing_fields)
                    raise HTTPException(
                        status_code=422, 
                        detail=f"The following fields are required for company orders: {field_list}"
                    )
            
            # Add audit fields
            update_dict['updated_by'] = current_user["id"]
            update_dict['updated_at'] = datetime.now(timezone.utc)
            
            # Serialize datetime fields
            prepared_update = prepare_for_mongo(update_dict)
            
            # Update the order
            result = await db.crane_orders.update_one(
                {"id": order_id},
                {"$set": prepared_update}
            )
            
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Log audit
            await log_audit(
                user_id=current_user["id"],
                user_email=current_user["email"],
                action="UPDATE",
                resource_type="ORDER",
                resource_id=order_id,
                old_data=existing_order,
                new_data=update_dict
            )
        
        # Fetch and return updated order
        updated_order = await db.crane_orders.find_one({"id": order_id}, {"_id": 0})
        return parse_from_mongo(updated_order)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error updating order: {str(e)}")

@api_router.delete("/orders/{order_id}")
async def delete_order(
    order_id: str,
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """Delete a specific crane order (Admin and Super Admin only)"""
    try:
        # Get order for audit log
        existing_order = await db.crane_orders.find_one({"id": order_id}, {"_id": 0})
        if not existing_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        result = await db.crane_orders.delete_one({"id": order_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Log audit
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action="DELETE",
            resource_type="ORDER",
            resource_id=order_id,
            old_data=existing_order
        )
        
        return {"message": "Order deleted successfully"}
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error deleting order: {str(e)}")

@api_router.get("/orders/stats/summary")
async def get_orders_summary(current_user: dict = Depends(get_current_user)):
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

# Audit endpoints
@api_router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN])),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (USER/ORDER)"),
    action: Optional[str] = Query(None, description="Filter by action (CREATE/UPDATE/DELETE/LOGIN/LOGOUT)"),
    user_email: Optional[str] = Query(None, description="Filter by user email"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    skip: int = Query(0, ge=0, description="Number of logs to skip")
):
    """Get audit logs (Admin and Super Admin only)"""
    query = {}
    
    if resource_type:
        query["resource_type"] = resource_type
    if action:
        query["action"] = action
    if user_email:
        query["user_email"] = {"$regex": user_email, "$options": "i"}
    
    try:
        logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        return [AuditLog(**parse_from_mongo(log)) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching audit logs: {str(e)}")

# Export endpoints
@api_router.get("/export/excel")
async def export_orders_excel(
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN])),
    order_type: Optional[str] = Query(None),
    customer_name: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=5000)
):
    """Export orders to Excel (Admin and Super Admin only)"""
    try:
        # Build query
        query = {}
        if order_type:
            query["order_type"] = order_type
        if customer_name:
            query["customer_name"] = {"$regex": customer_name, "$options": "i"}
        if phone:
            query["phone"] = {"$regex": phone, "$options": "i"}
        
        # Get orders
        orders = await db.crane_orders.find(query, {"_id": 0}).limit(limit).to_list(limit)
        
        # Create Excel workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Kawale Cranes Orders"
        
        # Headers
        headers = [
            "Order ID", "Date/Time", "Customer Name", "Phone", "Order Type",
            "Trip From", "Trip To", "Vehicle", "Driver", "Service Type",
            "Amount", "Advance", "KMs", "Toll", "Diesel", "Status"
        ]
        
        # Style headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        
        # Data rows
        for row, order in enumerate(orders, 2):
            parsed_order = parse_from_mongo(order)
            
            ws.cell(row, 1, parsed_order.get("unique_id", "")[:8])
            ws.cell(row, 2, parsed_order.get("date_time", "").strftime("%Y-%m-%d %H:%M") if parsed_order.get("date_time") else "")
            ws.cell(row, 3, parsed_order.get("customer_name", ""))
            ws.cell(row, 4, parsed_order.get("phone", ""))
            ws.cell(row, 5, parsed_order.get("order_type", "").title())
            
            if parsed_order.get("order_type") == "cash":
                ws.cell(row, 6, parsed_order.get("cash_trip_from", ""))
                ws.cell(row, 7, parsed_order.get("cash_trip_to", ""))
                ws.cell(row, 8, parsed_order.get("cash_vehicle_name", ""))
                ws.cell(row, 9, parsed_order.get("cash_driver_name", ""))
                ws.cell(row, 10, parsed_order.get("cash_service_type", ""))
                ws.cell(row, 11, parsed_order.get("amount_received", 0))
                ws.cell(row, 12, parsed_order.get("advance_amount", 0))
                ws.cell(row, 13, parsed_order.get("cash_kms_travelled", 0))
                ws.cell(row, 14, parsed_order.get("cash_toll", 0))
                ws.cell(row, 15, parsed_order.get("cash_diesel", 0))
            else:
                ws.cell(row, 6, parsed_order.get("company_trip_from", ""))
                ws.cell(row, 7, parsed_order.get("company_trip_to", ""))
                ws.cell(row, 8, parsed_order.get("company_vehicle_name", ""))
                ws.cell(row, 9, parsed_order.get("company_driver_name", ""))
                ws.cell(row, 10, parsed_order.get("company_service_type", ""))
                ws.cell(row, 11, "")  # No amount for company
                ws.cell(row, 12, "")  # No advance for company
                ws.cell(row, 13, parsed_order.get("company_kms_travelled", 0))
                ws.cell(row, 14, parsed_order.get("company_toll", 0))
                ws.cell(row, 15, parsed_order.get("company_diesel", 0))
            
            ws.cell(row, 16, "Active")
        
        # Adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to memory
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Log audit
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action="EXPORT",
            resource_type="ORDER",
            new_data={"format": "excel", "count": len(orders)}
        )
        
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=kawale_cranes_orders.xlsx"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting Excel: {str(e)}")

@api_router.get("/export/pdf")
async def export_orders_pdf(
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN])),
    order_type: Optional[str] = Query(None),
    customer_name: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=5000)
):
    """Export orders to PDF (Admin and Super Admin only)"""
    try:
        # Build query
        query = {}
        if order_type:
            query["order_type"] = order_type
        if customer_name:
            query["customer_name"] = {"$regex": customer_name, "$options": "i"}
        if phone:
            query["phone"] = {"$regex": phone, "$options": "i"}
        
        # Get orders
        orders = await db.crane_orders.find(query, {"_id": 0}).limit(limit).to_list(limit)
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#366092')
        )
        
        # Title
        story.append(Paragraph("Kawale Cranes - Orders Report", title_style))
        story.append(Spacer(1, 20))
        
        # Summary
        summary_data = [
            ['Total Orders', str(len(orders))],
            ['Report Generated', datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")],
            ['Generated By', current_user.get("full_name", "Admin")]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Orders table
        headers = ["ID", "Date", "Customer", "Phone", "Type", "Amount"]
        data = [headers]
        
        for order in orders:
            parsed_order = parse_from_mongo(order)
            row = [
                parsed_order.get("unique_id", "")[:8],
                parsed_order.get("date_time").strftime("%Y-%m-%d") if parsed_order.get("date_time") else "",
                parsed_order.get("customer_name", "")[:20],
                parsed_order.get("phone", ""),
                parsed_order.get("order_type", "").title(),
                f"₹{parsed_order.get('amount_received', 0)}" if parsed_order.get("order_type") == "cash" else "N/A"
            ]
            data.append(row)
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        
        # Log audit
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action="EXPORT",
            resource_type="ORDER",
            new_data={"format": "pdf", "count": len(orders)}
        )
        
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=kawale_cranes_orders.pdf"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting PDF: {str(e)}")

@api_router.get("/export/googlesheets")
async def export_orders_googlesheets(
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN])),
    order_type: Optional[str] = Query(None),
    customer_name: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=5000)
):
    """Export orders to Google Sheets (Admin and Super Admin only)"""
    try:
        # Check if Google Sheets credentials are configured
        service_account_key_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')
        spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        
        if not service_account_key_path or not spreadsheet_id:
            raise HTTPException(
                status_code=500, 
                detail="Google Sheets integration not configured. Please set GOOGLE_SERVICE_ACCOUNT_KEY_PATH and GOOGLE_SHEETS_SPREADSHEET_ID environment variables."
            )
        
        # Build query
        query = {}
        if order_type:
            query["order_type"] = order_type
        if customer_name:
            query["customer_name"] = {"$regex": customer_name, "$options": "i"}
        if phone:
            query["phone"] = {"$regex": phone, "$options": "i"}
        
        # Get orders
        orders = await db.crane_orders.find(query, {"_id": 0}).limit(limit).to_list(limit)
        
        if not orders:
            return {"message": "No orders found to export", "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"}
        
        # Set up Google Sheets API credentials
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Load credentials from file or environment variable
        if service_account_key_path.startswith('{'):
            # If it's JSON content as string
            credentials_info = json.loads(service_account_key_path)
            credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)
        else:
            # If it's a file path
            credentials = Credentials.from_service_account_file(service_account_key_path, scopes=scope)
        
        # Authorize and create gspread client
        gc = gspread.authorize(credentials)
        
        # Open the spreadsheet
        try:
            spreadsheet = gc.open_by_key(spreadsheet_id)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unable to access Google Spreadsheet. Please ensure the service account has access to the spreadsheet: {str(e)}"
            )
        
        # Create or get worksheet
        worksheet_name = f"Kawale_Orders_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
        try:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=len(orders)+10, cols=20)
        except Exception:
            # If adding worksheet fails, try to use the first sheet
            worksheet = spreadsheet.sheet1
            worksheet.clear()
        
        # Prepare headers and data
        headers = [
            "Order ID", "Date/Time", "Customer Name", "Phone", "Order Type", 
            "Trip From", "Trip To", "Vehicle Name", "Vehicle Number", "Driver",
            "Service Type", "Amount Received", "Advance Amount", "KM Travelled", 
            "Toll", "Diesel", "Diesel Location", "Care Off", "Care Off Amount", "Firm/Company"
        ]
        
        # Prepare data rows
        data_rows = [headers]
        
        for order in orders:
            parsed_order = parse_from_mongo(order)
            
            # Handle different fields based on order type
            if parsed_order.get("order_type") == "cash":
                trip_from = parsed_order.get("cash_trip_from", "")
                trip_to = parsed_order.get("cash_trip_to", "")
                vehicle_name = parsed_order.get("cash_vehicle_name", "")
                vehicle_number = parsed_order.get("cash_vehicle_number", "")
                driver = parsed_order.get("cash_driver_details", "")
                service_type = parsed_order.get("cash_service_type", "")
                km_travelled = parsed_order.get("cash_kms_travelled", 0)
                toll = parsed_order.get("cash_toll", 0)
                diesel = parsed_order.get("cash_diesel", "")
                diesel_location = parsed_order.get("cash_diesel_refill_location", "")
                care_off = parsed_order.get("care_off", "")
                care_off_amount = parsed_order.get("care_off_amount", 0)
                firm_company = parsed_order.get("name_of_firm", "")
            else:
                trip_from = parsed_order.get("company_trip_from", "")
                trip_to = parsed_order.get("company_trip_to", "")
                vehicle_name = parsed_order.get("company_vehicle_name", "")
                vehicle_number = parsed_order.get("company_vehicle_number", "")
                driver = parsed_order.get("company_driver_details", "")
                service_type = parsed_order.get("company_service_type", "")
                km_travelled = parsed_order.get("company_kms_travelled", 0)
                toll = parsed_order.get("company_toll", 0)
                diesel = parsed_order.get("company_diesel", "")
                diesel_location = parsed_order.get("company_diesel_refill_location", "")
                care_off = ""
                care_off_amount = 0
                firm_company = parsed_order.get("company_name", "")
            
            row = [
                parsed_order.get("unique_id", ""),
                parsed_order.get("date_time").strftime("%Y-%m-%d %H:%M") if parsed_order.get("date_time") else "",
                parsed_order.get("customer_name", ""),
                parsed_order.get("phone", ""),
                parsed_order.get("order_type", "").title(),
                trip_from,
                trip_to,
                vehicle_name,
                vehicle_number,
                driver,
                service_type,
                parsed_order.get("amount_received", 0) if parsed_order.get("order_type") == "cash" else "",
                parsed_order.get("advance_amount", 0) if parsed_order.get("order_type") == "cash" else "",
                km_travelled,
                toll,
                diesel,
                diesel_location,
                care_off,
                care_off_amount,
                firm_company
            ]
            data_rows.append(row)
        
        # Update the worksheet with all data at once (more efficient)
        worksheet.update(data_rows, value_input_option='USER_ENTERED')
        
        # Format header row
        try:
            worksheet.format('A1:T1', {
                "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                "horizontalAlignment": "CENTER"
            })
        except Exception:
            # Formatting is optional, continue if it fails
            pass
        
        # Log audit
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action="EXPORT",
            resource_type="ORDER",
            new_data={
                "format": "googlesheets", 
                "count": len(orders),
                "spreadsheet_id": spreadsheet_id,
                "worksheet": worksheet_name
            }
        )
        
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        
        return {
            "message": f"Successfully exported {len(orders)} orders to Google Sheets",
            "spreadsheet_url": spreadsheet_url,
            "worksheet_name": worksheet_name,
            "records_exported": len(orders)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting to Google Sheets: {str(e)}")

# Financial calculation endpoint
@api_router.get("/orders/{order_id}/financials")
async def get_order_financials(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get calculated financial details for an order"""
    try:
        # Get the order
        order = await db.crane_orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Calculate financials
        financials = await calculate_order_financials(order)
        
        return financials
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating financials: {str(e)}")

@api_router.get("/rates")
async def get_service_rates(
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """Get all service rates (Admin and Super Admin only)"""
    try:
        rates = await db.service_rates.find({}, {"_id": 0}).to_list(1000)
        return [parse_from_mongo(rate) for rate in rates]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching service rates: {str(e)}")

@api_router.put("/rates/{rate_id}")
async def update_service_rate(
    rate_id: str,
    update_data: dict,
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """Update a service rate (Admin and Super Admin only)"""
    try:
        # Validate the update data
        allowed_fields = ['base_rate', 'base_distance_km', 'rate_per_km_beyond']
        update_dict = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Validate numeric values
        for field, value in update_dict.items():
            if not isinstance(value, (int, float)) or value < 0:
                raise HTTPException(status_code=400, detail=f"{field} must be a non-negative number")
        
        # Add audit fields
        update_dict['updated_at'] = datetime.now(timezone.utc)
        
        # Prepare for MongoDB
        prepared_update = prepare_for_mongo(update_dict)
        
        # Update the rate
        result = await db.service_rates.update_one(
            {"id": rate_id},
            {"$set": prepared_update}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Service rate not found")
        
        # Log audit
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action="UPDATE",
            resource_type="SERVICE_RATE",
            resource_id=rate_id,
            new_data=update_dict
        )
        
        # Return updated rate
        updated_rate = await db.service_rates.find_one({"id": rate_id}, {"_id": 0})
        return parse_from_mongo(updated_rate)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating service rate: {str(e)}")

@api_router.post("/rates")
async def create_service_rate(
    rate_data: dict,
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """Create a new service rate (Admin and Super Admin only)"""
    try:
        # Validate required fields
        required_fields = ['name_of_firm', 'company_name', 'service_type', 'base_rate', 'rate_per_km_beyond']
        missing_fields = [field for field in required_fields if field not in rate_data or rate_data[field] is None]
        
        if missing_fields:
            field_list = ", ".join(missing_fields)
            raise HTTPException(status_code=400, detail=f"Missing required fields: {field_list}")
        
        # Check if rate combination already exists
        existing_rate = await db.service_rates.find_one({
            "name_of_firm": rate_data["name_of_firm"],
            "company_name": rate_data["company_name"],
            "service_type": rate_data["service_type"]
        })
        
        if existing_rate:
            raise HTTPException(
                status_code=400, 
                detail=f"Rate already exists for {rate_data['name_of_firm']} - {rate_data['company_name']} - {rate_data['service_type']}"
            )
        
        # Create new rate
        new_rate = ServiceRate(**rate_data)
        doc = prepare_for_mongo(new_rate.model_dump())
        
        result = await db.service_rates.insert_one(doc)
        
        # Log audit
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action="CREATE",
            resource_type="SERVICE_RATE",
            resource_id=new_rate.id,
            new_data=rate_data
        )
        
        return new_rate
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating service rate: {str(e)}")

@api_router.delete("/rates/{rate_id}")
async def delete_service_rate(
    rate_id: str,
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """Delete a service rate (Admin and Super Admin only)"""
    try:
        # Get rate for audit log
        existing_rate = await db.service_rates.find_one({"id": rate_id}, {"_id": 0})
        if not existing_rate:
            raise HTTPException(status_code=404, detail="Service rate not found")
        
        result = await db.service_rates.delete_one({"id": rate_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Service rate not found")
        
        # Log audit
        await log_audit(
            user_id=current_user["id"],
            user_email=current_user["email"],
            action="DELETE",
            resource_type="SERVICE_RATE",
            resource_id=rate_id,
            old_data=existing_rate
        )
        
        return {"message": "Service rate deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting service rate: {str(e)}")

# Reports endpoints
@api_router.get("/reports/expense-by-driver")
async def get_expense_report_by_driver(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2020, le=2030, description="Year (2020-2030)"),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """Get expense report by driver for a specific month (Admin and Super Admin only)"""
    try:
        # Create date range for the month
        start_date = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        
        # Query orders for the specified month
        query = {
            "date_time": {
                "$gte": start_date.isoformat(),
                "$lt": end_date.isoformat()
            }
        }
        
        orders = await db.crane_orders.find(query, {"_id": 0}).to_list(10000)
        parsed_orders = [parse_from_mongo(order) for order in orders]
        
        # Aggregate expenses by driver
        driver_expenses = {}
        
        for order in parsed_orders:
            # Determine driver name based on order type
            if order.get("order_type") == "cash":
                driver = order.get("cash_driver_name") or "Unknown Driver"
                diesel_cost = order.get("cash_diesel", 0) or 0
                toll_cost = order.get("cash_toll", 0) or 0
            else:  # company order
                driver = order.get("company_driver_name") or "Unknown Driver"
                diesel_cost = order.get("company_diesel", 0) or 0
                toll_cost = order.get("company_toll", 0) or 0
            
            if driver not in driver_expenses:
                driver_expenses[driver] = {
                    "driver_name": driver,
                    "cash_orders": 0,
                    "company_orders": 0,
                    "total_orders": 0,
                    "total_diesel_expense": 0,
                    "total_toll_expense": 0,
                    "total_expenses": 0
                }
            
            # Update counts
            if order.get("order_type") == "cash":
                driver_expenses[driver]["cash_orders"] += 1
            else:
                driver_expenses[driver]["company_orders"] += 1
            
            driver_expenses[driver]["total_orders"] += 1
            driver_expenses[driver]["total_diesel_expense"] += diesel_cost
            driver_expenses[driver]["total_toll_expense"] += toll_cost
            driver_expenses[driver]["total_expenses"] = (
                driver_expenses[driver]["total_diesel_expense"] + 
                driver_expenses[driver]["total_toll_expense"]
            )
        
        # Convert to list and sort by total expenses
        report_data = list(driver_expenses.values())
        report_data.sort(key=lambda x: x["total_expenses"], reverse=True)
        
        return {
            "month": month,
            "year": year,
            "report_type": "expense_by_driver",
            "data": report_data,
            "summary": {
                "total_drivers": len(report_data),
                "total_orders": sum(d["total_orders"] for d in report_data),
                "total_expenses": sum(d["total_expenses"] for d in report_data)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating expense report: {str(e)}")

@api_router.get("/reports/revenue-by-vehicle-type")
async def get_revenue_report_by_vehicle_type(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2020, le=2030, description="Year (2020-2030)"),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """Get revenue report by vehicle type for a specific month (Admin and Super Admin only)"""
    try:
        # Create date range for the month
        start_date = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        
        # Query orders for the specified month
        query = {
            "date_time": {
                "$gte": start_date.isoformat(),
                "$lt": end_date.isoformat()
            }
        }
        
        orders = await db.crane_orders.find(query, {"_id": 0}).to_list(10000)
        parsed_orders = [parse_from_mongo(order) for order in orders]
        
        # Aggregate revenue by vehicle type (service type)
        vehicle_revenue = {}
        
        for order in parsed_orders:
            # Determine service type based on order type
            if order.get("order_type") == "cash":
                service_type = order.get("cash_service_type") or "Unknown Service"
                # For cash orders, revenue is amount_received
                base_revenue = order.get("amount_received", 0) or 0
            else:  # company order
                service_type = order.get("company_service_type") or "Unknown Service"
                # For company orders, calculate revenue using rates
                financials = await calculate_order_financials(order)
                base_revenue = financials.base_revenue
            
            # Add incentive to revenue
            incentive_amount = order.get("incentive_amount", 0) or 0
            total_revenue = base_revenue + incentive_amount
            
            if service_type not in vehicle_revenue:
                vehicle_revenue[service_type] = {
                    "service_type": service_type,
                    "cash_orders": 0,
                    "company_orders": 0,
                    "total_orders": 0,
                    "total_base_revenue": 0,
                    "total_incentive_amount": 0,
                    "total_revenue": 0
                }
            
            # Update counts and revenue
            if order.get("order_type") == "cash":
                vehicle_revenue[service_type]["cash_orders"] += 1
            else:
                vehicle_revenue[service_type]["company_orders"] += 1
            
            vehicle_revenue[service_type]["total_orders"] += 1
            vehicle_revenue[service_type]["total_base_revenue"] += base_revenue
            vehicle_revenue[service_type]["total_incentive_amount"] += incentive_amount
            vehicle_revenue[service_type]["total_revenue"] += total_revenue
        
        # Convert to list and sort by total revenue
        report_data = list(vehicle_revenue.values())
        report_data.sort(key=lambda x: x["total_revenue"], reverse=True)
        
        return {
            "month": month,
            "year": year,
            "report_type": "revenue_by_vehicle_type",
            "data": report_data,
            "summary": {
                "total_service_types": len(report_data),
                "total_orders": sum(d["total_orders"] for d in report_data),
                "total_revenue": sum(d["total_revenue"] for d in report_data)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating revenue report: {str(e)}")

@api_router.get("/reports/expense-by-driver/export")
async def export_expense_report_by_driver(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2030),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """Export expense report by driver as Excel file"""
    try:
        # Get the report data
        report_response = await get_expense_report_by_driver(month, year, current_user)
        report_data = report_response["data"]
        
        # Create Excel workbook
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = f"Driver Expenses {year}-{month:02d}"
        
        # Headers
        headers = [
            "Driver Name", "Cash Orders", "Company Orders", "Total Orders",
            "Diesel Expenses (₹)", "Toll Expenses (₹)", "Total Expenses (₹)"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col, value=header)
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # Data rows
        for row_idx, driver_data in enumerate(report_data, 2):
            worksheet.cell(row=row_idx, column=1, value=driver_data["driver_name"])
            worksheet.cell(row=row_idx, column=2, value=driver_data["cash_orders"])
            worksheet.cell(row=row_idx, column=3, value=driver_data["company_orders"])
            worksheet.cell(row=row_idx, column=4, value=driver_data["total_orders"])
            worksheet.cell(row=row_idx, column=5, value=driver_data["total_diesel_expense"])
            worksheet.cell(row=row_idx, column=6, value=driver_data["total_toll_expense"])
            worksheet.cell(row=row_idx, column=7, value=driver_data["total_expenses"])
        
        # Summary row
        summary_row = len(report_data) + 3
        worksheet.cell(row=summary_row, column=1, value="TOTAL")
        worksheet.cell(row=summary_row, column=2, value=sum(d["cash_orders"] for d in report_data))
        worksheet.cell(row=summary_row, column=3, value=sum(d["company_orders"] for d in report_data))
        worksheet.cell(row=summary_row, column=4, value=sum(d["total_orders"] for d in report_data))
        worksheet.cell(row=summary_row, column=5, value=sum(d["total_diesel_expense"] for d in report_data))
        worksheet.cell(row=summary_row, column=6, value=sum(d["total_toll_expense"] for d in report_data))
        worksheet.cell(row=summary_row, column=7, value=sum(d["total_expenses"] for d in report_data))
        
        # Format summary row
        for col in range(1, 8):
            cell = worksheet.cell(row=summary_row, column=col)
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Save to bytes
        excel_buffer = BytesIO()
        workbook.save(excel_buffer)
        excel_buffer.seek(0)
        
        filename = f"kawale_expense_by_driver_{year}_{month:02d}.xlsx"
        
        return Response(
            content=excel_buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting expense report: {str(e)}")

@api_router.get("/reports/revenue-by-vehicle-type/export")
async def export_revenue_report_by_vehicle_type(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2030),
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
):
    """Export revenue report by vehicle type as Excel file"""
    try:
        # Get the report data
        report_response = await get_revenue_report_by_vehicle_type(month, year, current_user)
        report_data = report_response["data"]
        
        # Create Excel workbook
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = f"Vehicle Revenue {year}-{month:02d}"
        
        # Headers
        headers = [
            "Service Type", "Cash Orders", "Company Orders", "Total Orders",
            "Base Revenue (₹)", "Incentive Amount (₹)", "Total Revenue (₹)"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col, value=header)
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # Data rows
        for row_idx, vehicle_data in enumerate(report_data, 2):
            worksheet.cell(row=row_idx, column=1, value=vehicle_data["service_type"])
            worksheet.cell(row=row_idx, column=2, value=vehicle_data["cash_orders"])
            worksheet.cell(row=row_idx, column=3, value=vehicle_data["company_orders"])
            worksheet.cell(row=row_idx, column=4, value=vehicle_data["total_orders"])
            worksheet.cell(row=row_idx, column=5, value=vehicle_data["total_base_revenue"])
            worksheet.cell(row=row_idx, column=6, value=vehicle_data["total_incentive_amount"])
            worksheet.cell(row=row_idx, column=7, value=vehicle_data["total_revenue"])
        
        # Summary row
        summary_row = len(report_data) + 3
        worksheet.cell(row=summary_row, column=1, value="TOTAL")
        worksheet.cell(row=summary_row, column=2, value=sum(d["cash_orders"] for d in report_data))
        worksheet.cell(row=summary_row, column=3, value=sum(d["company_orders"] for d in report_data))
        worksheet.cell(row=summary_row, column=4, value=sum(d["total_orders"] for d in report_data))
        worksheet.cell(row=summary_row, column=5, value=sum(d["total_base_revenue"] for d in report_data))
        worksheet.cell(row=summary_row, column=6, value=sum(d["total_incentive_amount"] for d in report_data))
        worksheet.cell(row=summary_row, column=7, value=sum(d["total_revenue"] for d in report_data))
        
        # Format summary row
        for col in range(1, 8):
            cell = worksheet.cell(row=summary_row, column=col)
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Save to bytes
        excel_buffer = BytesIO()
        workbook.save(excel_buffer)
        excel_buffer.seek(0)
        
        filename = f"kawale_revenue_by_vehicle_type_{year}_{month:02d}.xlsx"
        
        return Response(
            content=excel_buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting revenue report: {str(e)}")

# Data import endpoint
@api_router.post("/import/excel")
async def import_excel_data(
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN])),
):
    """Import orders from Excel file (Admin and Super Admin only)"""
    # This endpoint will be implemented for file upload functionality
    return {"message": "Excel import functionality available. Use the frontend upload interface."}

# Service rates calculation functions
async def initialize_service_rates():
    """Initialize service rates from SK_Rates data"""
    try:
        # Check if rates already exist
        existing_rates = await db.service_rates.count_documents({})
        if existing_rates > 0:
            return  # Rates already initialized
        
        # SK_Rates data based on the provided Excel file
        rates_data = [
            # Kawale Cranes - Europ Assistance
            {"name_of_firm": "Kawale Cranes", "company_name": "Europ Assistance", "service_type": "2 Wheeler Towing", "base_rate": 1200, "rate_per_km_beyond": 12},
            {"name_of_firm": "Kawale Cranes", "company_name": "Europ Assistance", "service_type": "Under-lift", "base_rate": 1500, "rate_per_km_beyond": 15},
            {"name_of_firm": "Kawale Cranes", "company_name": "Europ Assistance", "service_type": "FBT", "base_rate": 1900, "rate_per_km_beyond": 21},
            
            # Vidharbha Towing - Europ Assistance  
            {"name_of_firm": "Vidharbha Towing", "company_name": "Europ Assistance", "service_type": "2 Wheeler Towing", "base_rate": 1200, "rate_per_km_beyond": 12},
            {"name_of_firm": "Vidharbha Towing", "company_name": "Europ Assistance", "service_type": "Under-lift", "base_rate": 1500, "rate_per_km_beyond": 15},
            {"name_of_firm": "Vidharbha Towing", "company_name": "Europ Assistance", "service_type": "FBT", "base_rate": 1900, "rate_per_km_beyond": 21},
            
            # Vira Towing - Europ Assistance
            {"name_of_firm": "Vira Towing", "company_name": "Europ Assistance", "service_type": "2 Wheeler Towing", "base_rate": 1200, "rate_per_km_beyond": 12},
            {"name_of_firm": "Vira Towing", "company_name": "Europ Assistance", "service_type": "Under-lift", "base_rate": 1500, "rate_per_km_beyond": 15},
            {"name_of_firm": "Vira Towing", "company_name": "Europ Assistance", "service_type": "FBT", "base_rate": 1900, "rate_per_km_beyond": 21},
            
            # Sarang Cranes - Europ Assistance
            {"name_of_firm": "Sarang Cranes", "company_name": "Europ Assistance", "service_type": "2 Wheeler Towing", "base_rate": 1200, "rate_per_km_beyond": 12},
            {"name_of_firm": "Sarang Cranes", "company_name": "Europ Assistance", "service_type": "Under-lift", "base_rate": 1500, "rate_per_km_beyond": 15},
            {"name_of_firm": "Sarang Cranes", "company_name": "Europ Assistance", "service_type": "FBT", "base_rate": 1900, "rate_per_km_beyond": 21},
            
            # Kawale Cranes - Mondial
            {"name_of_firm": "Kawale Cranes", "company_name": "Mondial", "service_type": "2 Wheeler Towing", "base_rate": 1200, "rate_per_km_beyond": 13},
            {"name_of_firm": "Kawale Cranes", "company_name": "Mondial", "service_type": "Under-lift", "base_rate": 1400, "rate_per_km_beyond": 15},
            
            # Vidharbha Towing - TVS
            {"name_of_firm": "Vidharbha Towing", "company_name": "TVS", "service_type": "Under-lift", "base_rate": 1700, "rate_per_km_beyond": 17},
            {"name_of_firm": "Vidharbha Towing", "company_name": "TVS", "service_type": "FBT", "base_rate": 2000, "rate_per_km_beyond": 20},
            
            # Vidharbha Towing - Mondial
            {"name_of_firm": "Vidharbha Towing", "company_name": "Mondial", "service_type": "FBT", "base_rate": 1700, "rate_per_km_beyond": 20},
        ]
        
        # Convert to ServiceRate objects and insert
        service_rates = []
        for rate_data in rates_data:
            service_rate = ServiceRate(**rate_data)
            service_rates.append(prepare_for_mongo(service_rate.model_dump()))
        
        await db.service_rates.insert_many(service_rates)
        logging.info(f"Initialized {len(service_rates)} service rates")
        
    except Exception as e:
        logging.error(f"Error initializing service rates: {str(e)}")

async def calculate_order_financials(order: dict) -> CalculatedOrderFinancials:
    """Calculate financial details for a company order based on rates"""
    try:
        # Only calculate for company orders
        if order.get("order_type") != "company":
            return CalculatedOrderFinancials()
        
        # Extract required fields
        name_of_firm = order.get("name_of_firm", "")
        company_name = order.get("company_name", "")
        service_type = order.get("company_service_type", "")
        kms_travelled = order.get("company_kms_travelled", 0) or 0
        incentive_amount = order.get("incentive_amount", 0) or 0
        
        if not all([name_of_firm, company_name, service_type]):
            return CalculatedOrderFinancials(
                incentive_amount=incentive_amount,
                total_revenue=incentive_amount,
                calculation_details="Missing firm, company, or service type information"
            )
        
        # Find matching rate
        rate_query = {
            "name_of_firm": name_of_firm,
            "company_name": company_name,
            "service_type": service_type
        }
        
        rate_doc = await db.service_rates.find_one(rate_query, {"_id": 0})
        
        if not rate_doc:
            return CalculatedOrderFinancials(
                incentive_amount=incentive_amount,
                total_revenue=incentive_amount,
                calculation_details=f"No rate found for {name_of_firm} - {company_name} - {service_type}"
            )
        
        # Calculate base revenue
        base_rate = rate_doc.get("base_rate", 0)
        base_distance = rate_doc.get("base_distance_km", 40)
        rate_per_km_beyond = rate_doc.get("rate_per_km_beyond", 0)
        
        if kms_travelled <= base_distance:
            base_revenue = base_rate
            calculation_details = f"Base rate: ₹{base_rate} for {kms_travelled}km (≤{base_distance}km)"
        else:
            excess_km = kms_travelled - base_distance
            excess_charges = excess_km * rate_per_km_beyond
            base_revenue = base_rate + excess_charges
            calculation_details = f"Base: ₹{base_rate} + Extra {excess_km}km × ₹{rate_per_km_beyond} = ₹{base_revenue}"
        
        total_revenue = base_revenue + incentive_amount
        
        if incentive_amount > 0:
            calculation_details += f" + Incentive: ₹{incentive_amount}"
        
        return CalculatedOrderFinancials(
            base_revenue=base_revenue,
            incentive_amount=incentive_amount,
            total_revenue=total_revenue,
            calculation_details=calculation_details
        )
        
    except Exception as e:
        logging.error(f"Error calculating order financials: {str(e)}")
        return CalculatedOrderFinancials(
            incentive_amount=order.get("incentive_amount", 0) or 0,
            total_revenue=order.get("incentive_amount", 0) or 0,
            calculation_details=f"Calculation error: {str(e)}"
        )

# Initialize default super admin user
async def create_default_super_admin():
    """Create default super admin user if none exists"""
    existing_admin = await db.users.find_one({"role": "super_admin"})
    if not existing_admin:
        default_admin = User(
            email="admin@kawalecranes.com",
            full_name="Super Administrator",
            role=UserRole.SUPER_ADMIN
        )
        
        admin_doc = prepare_for_mongo(default_admin.model_dump())
        admin_doc["hashed_password"] = get_password_hash("admin123")
        
        await db.users.insert_one(admin_doc)
        print("Default super admin created: admin@kawalecranes.com / admin123")

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

@app.on_event("startup")
async def startup_event():
    await create_default_super_admin()
    await initialize_service_rates()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
