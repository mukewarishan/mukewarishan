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
    
    datetime_fields = ['added_time', 'date_time', 'reach_time', 'drop_time', 'created_at', 'updated_at', 'last_login', 'timestamp']
    for field in datetime_fields:
        if field in item and isinstance(item[field], str):
            try:
                item[field] = datetime.fromisoformat(item[field])
            except ValueError:
                continue
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
