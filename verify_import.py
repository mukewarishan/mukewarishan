import os
from pymongo import MongoClient

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
orders_collection = db['crane_orders']

print("=" * 60)
print("VERIFICATION OF IMPORTED DATA")
print("=" * 60)

# Count by order type
cash_count = orders_collection.count_documents({'order_type': 'cash'})
company_count = orders_collection.count_documents({'order_type': 'company'})

print(f"\nTotal orders: {orders_collection.count_documents({})}")
print(f"Cash orders: {cash_count}")
print(f"Company orders: {company_count}")

# Show a sample cash order
print("\n" + "=" * 60)
print("SAMPLE CASH ORDER:")
print("=" * 60)
cash_order = orders_collection.find_one({'order_type': 'cash'})
if cash_order:
    print(f"ID: {cash_order.get('id')}")
    print(f"Customer Name: {cash_order.get('customer_name')}")
    print(f"Phone: {cash_order.get('phone')}")
    print(f"Date-Time: {cash_order.get('date_time')}")
    print(f"Trip From: {cash_order.get('cash_trip_from')}")
    print(f"Trip To: {cash_order.get('cash_trip_to')}")
    print(f"Driver: {cash_order.get('cash_driver_name')}")
    print(f"Service Type: {cash_order.get('cash_service_type')}")
    print(f"Amount Received: {cash_order.get('amount_received')}")

# Show a sample company order
print("\n" + "=" * 60)
print("SAMPLE COMPANY ORDER:")
print("=" * 60)
company_order = orders_collection.find_one({'order_type': 'company'})
if company_order:
    print(f"ID: {company_order.get('id')}")
    print(f"Customer Name: {company_order.get('customer_name')}")
    print(f"Phone: {company_order.get('phone')}")
    print(f"Date-Time: {company_order.get('date_time')}")
    print(f"Company Name: {company_order.get('company_name')}")
    print(f"Case ID: {company_order.get('case_id_file_number')}")
    print(f"Driver: {company_order.get('company_driver_name')}")
    print(f"Service Type: {company_order.get('company_service_type')}")
    print(f"Trip From: {company_order.get('company_trip_from')}")
    print(f"Trip To: {company_order.get('company_trip_to')}")
    print(f"Reach Time: {company_order.get('reach_time')}")
    print(f"Drop Time: {company_order.get('drop_time')}")

print("\n" + "=" * 60)
