import os
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Get some sample orders
sample_orders = list(db.crane_orders.find({'created_by': 'system_import'}).limit(5))

# Create sample data preview
sample_data = []
for order in sample_orders:
    sample_data.append({
        'customer_name': order.get('customer_name', 'Unknown'),
        'phone': order.get('phone', 'N/A'),
        'order_type': order.get('order_type', 'N/A'),
        'date_time': order.get('date_time', datetime.now(timezone.utc).isoformat())
    })

# Count cash and company orders
cash_orders = db.crane_orders.count_documents({'created_by': 'system_import', 'order_type': 'cash'})
company_orders = db.crane_orders.count_documents({'created_by': 'system_import', 'order_type': 'company'})
total_imported = db.crane_orders.count_documents({'created_by': 'system_import'})

# Create import history record
import_history = {
    'id': str(uuid.uuid4()),
    'filename': 'Kawale_Cranes_23092025.xlsx',
    'imported_by': 'System Admin',
    'imported_by_email': 'admin@kawalecranes.com',
    'imported_at': datetime.now(timezone.utc).isoformat(),
    'total_records': total_imported,
    'success_count': total_imported,
    'error_count': 0,
    'cash_orders': cash_orders,
    'company_orders': company_orders,
    'sample_data': sample_data
}

# Insert into database
result = db.import_history.insert_one(import_history)
print(f"✅ Sample import history added with ID: {import_history['id']}")
print(f"Total records: {total_imported}")
print(f"Cash orders: {cash_orders}")
print(f"Company orders: {company_orders}")
print(f"Sample data count: {len(sample_data)}")
