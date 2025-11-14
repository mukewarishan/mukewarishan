import os
from pymongo import MongoClient
import bcrypt

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Find admin user
admin_user = db.users.find_one({"email": "admin@kawalecranes.com"})

if admin_user:
    print(f"Found admin user: {admin_user['full_name']} ({admin_user['email']})")
    
    # Reset password to 'admin123'
    new_password = "admin123"
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update password
    result = db.users.update_one(
        {"email": "admin@kawalecranes.com"},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    if result.modified_count > 0:
        print(f"✅ Password reset successfully!")
        print(f"Email: admin@kawalecranes.com")
        print(f"Password: admin123")
    else:
        print("⚠️ Password was already set correctly")
else:
    print("❌ Admin user not found!")
    print("Creating new admin user...")
    
    # Create admin user
    import uuid
    from datetime import datetime, timezone
    
    hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    admin_data = {
        "id": str(uuid.uuid4()),
        "email": "admin@kawalecranes.com",
        "hashed_password": hashed_password,
        "full_name": "Super Administrator",
        "role": "super_admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    db.users.insert_one(admin_data)
    print("✅ Admin user created successfully!")
    print(f"Email: admin@kawalecranes.com")
    print(f"Password: admin123")
