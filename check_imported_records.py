import os
from pymongo import MongoClient

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
orders_collection = db['crane_orders']

print("=" * 60)
print("CHECKING FOR SPECIFIC IMPORTED RECORDS")
print("=" * 60)

# Check for Kartik cash order
print("\n1. Looking for Kartik cash order (phone: 7350009241):")
kartik_order = orders_collection.find_one({'phone': '7350009241'})
if kartik_order:
    print(f"✅ FOUND: {kartik_order.get('customer_name')}")
    print(f"   Order Type: {kartik_order.get('order_type')}")
    print(f"   Driver: {kartik_order.get('cash_driver_name')}")
    print(f"   Service Type: {kartik_order.get('cash_service_type')}")
    print(f"   Amount: ₹{kartik_order.get('amount_received')}")
    print(f"   Date: {kartik_order.get('date_time')}")
else:
    print("❌ NOT FOUND")

# Check for Sachi company order
print("\n2. Looking for Sachi company order (phone: 9545617572):")
sachi_order = orders_collection.find_one({'phone': '9545617572'})
if sachi_order:
    print(f"✅ FOUND: {sachi_order.get('customer_name')}")
    print(f"   Order Type: {sachi_order.get('order_type')}")
    print(f"   Company: {sachi_order.get('company_name')}")
    print(f"   Driver: {sachi_order.get('company_driver_name')}")
    print(f"   Service Type: {sachi_order.get('company_service_type')}")
    print(f"   Date: {sachi_order.get('date_time')}")
    print(f"   Reach Time: {sachi_order.get('reach_time')}")
    print(f"   Drop Time: {sachi_order.get('drop_time')}")
else:
    print("❌ NOT FOUND")

# Check date range of imported data
print("\n3. Checking date range of all orders:")
orders_by_created_by = orders_collection.aggregate([
    {"$match": {"created_by": "system_import"}},
    {"$project": {"date_time": 1}},
    {"$sort": {"date_time": 1}}
])
import_dates = list(orders_by_created_by)
if import_dates:
    print(f"   Total imported orders: {len(import_dates)}")
    print(f"   Earliest date: {import_dates[0]['date_time']}")
    print(f"   Latest date: {import_dates[-1]['date_time']}")
else:
    print("   No orders with created_by='system_import' found")

# Check for September 2025 data
print("\n4. Checking September 2025 data:")
sept_2025_count = orders_collection.count_documents({
    'date_time': {
        '$gte': '2025-09-01T00:00:00',
        '$lt': '2025-10-01T00:00:00'
    }
})
print(f"   Orders in September 2025: {sept_2025_count}")

# Check for specific drivers from import
print("\n5. Checking for specific drivers from import:")
drivers = ['Meshram', 'Akshay', 'Vikas', 'Anup']
for driver in drivers:
    cash_count = orders_collection.count_documents({'cash_driver_name': driver})
    company_count = orders_collection.count_documents({'company_driver_name': driver})
    total = cash_count + company_count
    if total > 0:
        print(f"   ✅ {driver}: {total} orders (Cash: {cash_count}, Company: {company_count})")
    else:
        print(f"   ❌ {driver}: Not found")

print("\n" + "=" * 60)
