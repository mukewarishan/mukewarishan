#!/usr/bin/env python3

import pandas as pd
import requests
import sys
import os
import re
from datetime import datetime, timezone
import json
import uuid

class KawaleCranesDataImporter:
    def __init__(self, excel_file_url, api_base_url="https://kawale-data.preview.emergentagent.com/api"):
        self.excel_file_url = excel_file_url
        self.api_base_url = api_base_url
        self.access_token = None
        self.imported_count = 0
        self.failed_count = 0
        self.failed_records = []
        
    def authenticate(self, email="admin@kawalecranes.com", password="admin123"):
        """Authenticate with the API to get access token"""
        login_data = {"email": email, "password": password}
        
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                print(f"✅ Authenticated successfully as {data.get('user', {}).get('full_name')}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def download_and_parse_excel(self):
        """Download and parse the Excel file"""
        try:
            print("📥 Downloading Excel file...")
            
            # Download the file
            response = requests.get(self.excel_file_url, timeout=30)
            response.raise_for_status()
            
            # Save temporarily
            temp_file = "/tmp/kawale_cranes_data.xlsx"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            # Read Excel file
            print("📊 Parsing Excel data...")
            df = pd.read_excel(temp_file)
            
            # Clean up temp file
            os.remove(temp_file)
            
            print(f"✅ Loaded {len(df)} rows from Excel file")
            print(f"📋 Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error downloading/parsing Excel: {str(e)}")
            return None
    
    def clean_currency_value(self, value):
        """Clean currency values and convert to float"""
        if pd.isna(value) or value in ['NA', 'na', 'N/A', 'Unknown', '', ' ']:
            return None
        
        if isinstance(value, str):
            # Remove currency symbols and text
            cleaned = re.sub(r'[₹INR\s,]', '', str(value))
            cleaned = re.sub(r'\.00$', '', cleaned)  # Remove .00 endings
            
            try:
                return float(cleaned) if cleaned else None
            except ValueError:
                return None
        
        try:
            return float(value) if value != 0 else None
        except (ValueError, TypeError):
            return None
    
    def clean_text_value(self, value):
        """Clean text values"""
        if pd.isna(value) or value in ['NA', 'na', 'N/A', 'Unknown', '', ' ']:
            return None
        return str(value).strip() if str(value).strip() else None
    
    def determine_order_type(self, row):
        """Determine if this is a cash or company order based on available data"""
        # Check if there's company-specific data
        company_indicators = [
            'Name of Firm', 'Company Name', 'Case ID / File Number',
            'Company Vehicle Name (Make & Model)', 'Company Vehicle Number',
            'Company Service Type'
        ]
        
        has_company_data = any(
            self.clean_text_value(row.get(col)) for col in company_indicators if col in row
        )
        
        # Check for explicit cash/company indicator in the data
        cash_company_field = row.get('Cash / Company', '')
        if isinstance(cash_company_field, str):
            if 'company' in cash_company_field.lower():
                return 'company'
            elif 'cash' in cash_company_field.lower():
                return 'cash'
        
        # Default logic: if has company data, it's company, otherwise cash
        return 'company' if has_company_data else 'cash'
    
    def parse_datetime(self, value):
        """Parse datetime values"""
        if pd.isna(value) or value in ['NA', 'na', 'N/A', '', ' ']:
            return datetime.now(timezone.utc)
        
        # If it's already a datetime
        if isinstance(value, datetime):
            return value.replace(tzinfo=timezone.utc)
        
        # Try to parse string
        try:
            # Try common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    return datetime.strptime(str(value), fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            
            # If all fails, return current time
            return datetime.now(timezone.utc)
        except:
            return datetime.now(timezone.utc)
    
    def extract_phone_number(self, customer_name, phone_field):
        """Extract phone number from various fields"""
        # First try the phone field
        if self.clean_text_value(phone_field):
            phone = re.sub(r'[^\d+]', '', str(phone_field))
            if len(phone) >= 10:
                return phone[-10:]  # Get last 10 digits
        
        # Try to extract from customer name or other fields
        if self.clean_text_value(customer_name):
            phone_match = re.search(r'(\d{10,})', str(customer_name))
            if phone_match:
                return phone_match.group(1)[-10:]
        
        # Generate a default phone number
        return f"9999{str(uuid.uuid4().int)[:6]}"
    
    def transform_row_to_order(self, row, index):
        """Transform Excel row to order format"""
        try:
            # Determine order type
            order_type = self.determine_order_type(row)
            
            # Extract basic info
            customer_name = self.clean_text_value(row.get('Customer Name', f'Customer_{index}'))
            if not customer_name:
                customer_name = f'Customer_{index}'
            
            phone = self.extract_phone_number(
                customer_name, 
                row.get('Phone', '')
            )
            
            # Create base order
            order_data = {
                'customer_name': customer_name,
                'phone': phone,
                'order_type': order_type,
                'date_time': self.parse_datetime(row.get('Date-Time')).isoformat()
            }
            
            if order_type == 'cash':
                # Cash order fields
                order_data.update({
                    'cash_trip_from': self.clean_text_value(row.get('Cash Trip From:')),
                    'cash_trip_to': self.clean_text_value(row.get('Cash Trip To:')),
                    'care_off': self.clean_text_value(row.get('Care Off')),
                    'care_off_amount': self.clean_currency_value(row.get('Care Off Amount')),
                    'cash_vehicle_details': self.clean_text_value(row.get('Cash Vehicle Details')),
                    'cash_driver_details': self.clean_text_value(row.get('Cash Driver Details')),
                    'cash_vehicle_name': self.clean_text_value(row.get('Cash Vehicle Name (Make & Model)')),
                    'cash_vehicle_number': self.clean_text_value(row.get('Cash Vehicle Number')),
                    'cash_service_type': self.clean_text_value(row.get('Cash Service Type')),
                    'amount_received': self.clean_currency_value(row.get('Amount Received')),
                    'advance_amount': self.clean_currency_value(row.get('Advance Amount')),
                    'cash_kms_travelled': self.clean_currency_value(row.get('Cash Kms Travelled')),
                    'cash_toll': self.clean_currency_value(row.get('Cash Toll')),
                    'cash_diesel': self.clean_currency_value(row.get('Diesel Cash Diesel')),
                    'cash_diesel_refill_location': self.clean_text_value(row.get('Cash Diesel Re-fill Location'))
                })
            else:
                # Company order fields
                order_data.update({
                    'name_of_firm': self.clean_text_value(row.get('Name of Firm')) or self.clean_text_value(row.get('Diesel Name of Firm')),
                    'company_name': self.clean_text_value(row.get('Company Name')),
                    'case_id_file_number': self.clean_text_value(row.get('Case ID / File Number')),
                    'company_vehicle_name': self.clean_text_value(row.get('Company Vehicle Name (Make & Model)')),
                    'company_vehicle_number': self.clean_text_value(row.get('Company Vehicle Number')),
                    'company_service_type': self.clean_text_value(row.get('Company Service Type')),
                    'company_vehicle_details': self.clean_text_value(row.get('Company Vehicle Details')),
                    'company_driver_details': self.clean_text_value(row.get('Company Driver Details')),
                    'company_trip_from': self.clean_text_value(row.get('Company Trip From:')),
                    'company_trip_to': self.clean_text_value(row.get('Company Trip To:')),
                    'company_kms_travelled': self.clean_currency_value(row.get('Company Kms Travelled')),
                    'company_toll': self.clean_currency_value(row.get('Company Toll')),
                    'company_diesel': self.clean_currency_value(row.get('Company Diesel Company Diesel')),
                    'company_diesel_refill_location': self.clean_text_value(row.get('Company Diesel Re-fill Location'))
                })
                
                # Parse times for company orders
                if self.clean_text_value(row.get('Reach Time')):
                    try:
                        order_data['reach_time'] = self.parse_datetime(row.get('Reach Time')).isoformat()
                    except:
                        pass
                        
                if self.clean_text_value(row.get('Drop Time')):
                    try:
                        order_data['drop_time'] = self.parse_datetime(row.get('Drop Time')).isoformat()
                    except:
                        pass
            
            return order_data
            
        except Exception as e:
            print(f"❌ Error transforming row {index}: {str(e)}")
            return None
    
    def import_order(self, order_data, index):
        """Import a single order via API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.post(
                f"{self.api_base_url}/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.imported_count += 1
                print(f"✅ Imported order {index}: {order_data['customer_name']} ({order_data['order_type']})")
                return True
            else:
                self.failed_count += 1
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"❌ Failed to import order {index}: {response.status_code} - {error_data}")
                self.failed_records.append({'index': index, 'data': order_data, 'error': error_data})
                return False
                
        except Exception as e:
            self.failed_count += 1
            print(f"❌ Error importing order {index}: {str(e)}")
            self.failed_records.append({'index': index, 'data': order_data, 'error': str(e)})
            return False
    
    def import_data(self):
        """Main import process"""
        print("🚀 Starting Kawale Cranes data import...")
        
        # Authenticate
        if not self.authenticate():
            return False
        
        # Download and parse Excel
        df = self.download_and_parse_excel()
        if df is None:
            return False
        
        print(f"\n📋 Processing {len(df)} records...")
        
        # Process each row
        for index, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.get('Customer Name')) and pd.isna(row.get('Phone')) and pd.isna(row.get('Date-Time')):
                continue
            
            # Transform row to order format
            order_data = self.transform_row_to_order(row, index + 1)
            if order_data:
                # Import the order
                self.import_order(order_data, index + 1)
        
        # Print summary
        print(f"\n📊 Import Summary:")
        print(f"✅ Successfully imported: {self.imported_count} orders")
        print(f"❌ Failed imports: {self.failed_count} orders")
        
        if self.failed_records:
            print(f"\n❌ Failed Records:")
            for record in self.failed_records[:5]:  # Show first 5 failed records
                print(f"   Row {record['index']}: {record['error']}")
        
        return True

def main():
    """Main function"""
    # Excel file URL from the user
    excel_url = "https://customer-assets.emergentagent.com/job_wheelerdata-entry/artifacts/hxo9vs6w_Kawale_Cranes_23092025.xlsx"
    
    # Create importer and run
    importer = KawaleCranesDataImporter(excel_url)
    success = importer.import_data()
    
    if success:
        print("🎉 Data import completed!")
    else:
        print("💥 Data import failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()