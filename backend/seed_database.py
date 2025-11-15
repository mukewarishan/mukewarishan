import pandas as pd
import os
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
import re
import bcrypt

def clean_monetary_value(value):
    """Clean monetary values like '₹ 2000.00', '500.00 INR', etc."""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value_str = str(value).strip()
    cleaned = re.sub(r'[₹,\s]|INR', '', value_str)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

def clean_string(value):
    """Clean string values, return None for NaN or 'NaN' strings"""
    if pd.isna(value) or value is None:
        return None
    value_str = str(value).strip()
    if value_str.lower() in ['nan', 'nat', 'na', 'unknown', '']:
        return None
    return value_str

def ensure_super_admin_exists(db):
    """Ensure super admin user exists in the database"""
    try:
        import bcrypt
        users_collection = db['users']
        
        # Check if super admin exists
        super_admin = users_collection.find_one({"email": "ad@kc.com"})
        
        if not super_admin:
            # Create super admin user
            hashed_password = bcrypt.hashpw("jaishriram".encode('utf-8'), bcrypt.gensalt())
            
            user = {
                "id": str(uuid.uuid4()),
                "email": "ad@kc.com",
                "full_name": "Super Administrator",
                "hashed_password": hashed_password.decode('utf-8'),
                "role": "super_admin",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            users_collection.insert_one(user)
            print("[SEED] ✅ Created super admin user: ad@kc.com / jaishriram")
        else:
            # Update password to ensure it's correct
            hashed_password = bcrypt.hashpw("jaishriram".encode('utf-8'), bcrypt.gensalt())
            users_collection.update_one(
                {"email": "ad@kc.com"},
                {"$set": {"hashed_password": hashed_password.decode('utf-8')}}
            )
            print("[SEED] ✅ Super admin user exists, password updated: ad@kc.com / jaishriram")
            
    except Exception as e:
        print(f"[SEED] Error creating super admin: {str(e)}")

def seed_database_if_empty():
    """Seed database with Excel data if it's empty or has very few records"""
    try:
        # MongoDB connection
        MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        DB_NAME = os.environ.get('DB_NAME', 'test_database')
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        orders_collection = db['crane_orders']
        
        # Always ensure super admin exists
        ensure_super_admin_exists(db)
        
        # Check if database already has data
        existing_count = orders_collection.count_documents({})
        print(f"[SEED] Current order count in database: {existing_count}")
        
        # Check if imported data already exists
        imported_count = orders_collection.count_documents({'created_by': 'system_import'})
        print(f"[SEED] Imported records count: {imported_count}")
        
        # Only seed if no imported data exists
        if imported_count > 0:
            print(f"[SEED] Database already has {imported_count} imported records. Skipping seed.")
            return False
        
        # Path to seed data file
        seed_file = os.path.join(os.path.dirname(__file__), 'seed_data.xlsx')
        
        if not os.path.exists(seed_file):
            print(f"[SEED] Seed file not found at {seed_file}. Skipping seed.")
            return False
        
        print(f"[SEED] Starting database seed from {seed_file}...")
        
        # Read Excel file
        df = pd.read_excel(seed_file)
        print(f"[SEED] Found {len(df)} records to import")
        
        imported_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Determine order type
                order_type_raw = clean_string(row.get('Cash / Company', ''))
                if not order_type_raw:
                    error_count += 1
                    continue
                
                order_type = order_type_raw.lower()
                
                # Base order data
                order_data = {
                    'id': str(uuid.uuid4()),
                    'unique_id': str(uuid.uuid4()),
                    'added_time': row['Added Time'].isoformat() if pd.notna(row['Added Time']) else datetime.now(timezone.utc).isoformat(),
                    'ip_address': clean_string(row.get('IP Address')),
                    'date_time': row['Date-Time'].isoformat() if pd.notna(row['Date-Time']) else datetime.now(timezone.utc).isoformat(),
                    'customer_name': clean_string(row.get('Customer Name', 'Unknown')),
                    'phone': str(row.get('Phone', '')),
                    'order_type': order_type,
                    'created_by': 'system_import',
                    'updated_by': None,
                    'updated_at': None,
                }
                
                # Initialize all fields
                order_data.update({
                    'incentive_amount': None,
                    'incentive_reason': None,
                    'incentive_added_by': None,
                    'incentive_added_at': None,
                    'cash_trip_from': None,
                    'cash_trip_to': None,
                    'care_off': None,
                    'care_off_amount': None,
                    'cash_vehicle_details': None,
                    'cash_driver_details': None,
                    'cash_vehicle_name': None,
                    'cash_vehicle_number': None,
                    'cash_service_type': None,
                    'amount_received': None,
                    'advance_amount': None,
                    'cash_kms_travelled': None,
                    'cash_toll': None,
                    'diesel': None,
                    'cash_diesel': None,
                    'cash_diesel_refill_location': None,
                    'cash_driver_name': None,
                    'cash_towing_vehicle': None,
                    'name_of_firm': None,
                    'company_name': None,
                    'case_id_file_number': None,
                    'company_vehicle_name': None,
                    'company_vehicle_number': None,
                    'company_service_type': None,
                    'company_vehicle_details': None,
                    'company_driver_details': None,
                    'company_trip_from': None,
                    'company_trip_to': None,
                    'reach_time': None,
                    'drop_time': None,
                    'company_kms_travelled': None,
                    'company_toll': None,
                    'diesel_name': None,
                    'company_diesel': None,
                    'company_diesel_refill_location': None,
                    'company_driver_name': None,
                    'company_towing_vehicle': None,
                })
                
                # Populate fields based on order type
                if order_type == 'cash':
                    order_data['cash_trip_from'] = clean_string(row.get('Cash Trip From:'))
                    order_data['cash_trip_to'] = clean_string(row.get('Cash Trip To:'))
                    order_data['care_off'] = clean_string(row.get('Care Off'))
                    order_data['care_off_amount'] = clean_monetary_value(row.get('Care Off Amount'))
                    order_data['cash_vehicle_details'] = clean_string(row.get('Cash Vehicle Details'))
                    order_data['cash_driver_details'] = clean_string(row.get('Cash Driver Details'))
                    order_data['cash_vehicle_name'] = clean_string(row.get('Cash Vehicle Name (Make & Model)'))
                    order_data['cash_vehicle_number'] = clean_string(row.get('Cash Vehicle Number'))
                    order_data['cash_service_type'] = clean_string(row.get('Cash Service Type'))
                    order_data['amount_received'] = clean_monetary_value(row.get('Amount'))
                    order_data['advance_amount'] = clean_monetary_value(row.get('Received Advance Amount'))
                    order_data['cash_kms_travelled'] = row.get('Cash Kms Travelled') if pd.notna(row.get('Cash Kms Travelled')) else None
                    order_data['cash_toll'] = clean_monetary_value(row.get('Cash Toll'))
                    order_data['diesel'] = clean_string(row.get('Diesel'))
                    order_data['cash_diesel'] = row.get('Cash Diesel') if pd.notna(row.get('Cash Diesel')) else None
                    order_data['cash_diesel_refill_location'] = clean_string(row.get('Cash Diesel Re-fill Location'))
                    order_data['cash_driver_name'] = order_data['cash_driver_details']
                    order_data['cash_towing_vehicle'] = order_data['cash_vehicle_details']
                    
                elif order_type == 'company':
                    order_data['name_of_firm'] = clean_string(row.get('Name of Firm'))
                    order_data['company_name'] = clean_string(row.get('Company Name'))
                    order_data['case_id_file_number'] = clean_string(row.get('Case ID / File Number'))
                    order_data['company_vehicle_name'] = clean_string(row.get('Company Vehicle Name (Make & Model)'))
                    order_data['company_vehicle_number'] = clean_string(row.get('Company Vehicle Number'))
                    order_data['company_service_type'] = clean_string(row.get('Company Service Type'))
                    order_data['company_vehicle_details'] = clean_string(row.get('Company Vehicle Details'))
                    order_data['company_driver_details'] = clean_string(row.get('Company Driver Details'))
                    order_data['company_trip_from'] = clean_string(row.get('Company Trip From:'))
                    order_data['company_trip_to'] = clean_string(row.get('Company Trip To:'))
                    
                    reach_time = row.get('Reach Time')
                    if pd.notna(reach_time) and isinstance(reach_time, pd.Timestamp):
                        order_data['reach_time'] = reach_time.isoformat()
                    
                    drop_time = row.get('Drop Time')
                    if pd.notna(drop_time) and isinstance(drop_time, pd.Timestamp):
                        order_data['drop_time'] = drop_time.isoformat()
                    
                    order_data['company_kms_travelled'] = row.get('Company Kms Travelled') if pd.notna(row.get('Company Kms Travelled')) else None
                    order_data['company_toll'] = clean_monetary_value(row.get('Company Toll'))
                    order_data['company_diesel'] = row.get('Company Diesel') if pd.notna(row.get('Company Diesel')) else None
                    order_data['company_diesel_refill_location'] = clean_string(row.get('Company Diesel Re-fill Location'))
                    order_data['company_driver_name'] = order_data['company_driver_details']
                    order_data['company_towing_vehicle'] = order_data['company_vehicle_details']
                
                # Insert into MongoDB
                orders_collection.insert_one(order_data)
                imported_count += 1
                
            except Exception as e:
                print(f"[SEED] Error importing row {index + 1}: {str(e)}")
                error_count += 1
                continue
        
        print(f"[SEED] Database seeding complete!")
        print(f"[SEED] Successfully imported: {imported_count} records")
        print(f"[SEED] Errors: {error_count}")
        print(f"[SEED] Total orders in database: {orders_collection.count_documents({})}")
        
        return True
        
    except Exception as e:
        print(f"[SEED] Error during database seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    seed_database_if_empty()
