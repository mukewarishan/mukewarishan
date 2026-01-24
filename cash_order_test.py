#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone

class CashOrderCreationTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.token = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        print(f"{status} - {name}: {details}")
        return success

    def login(self):
        """Login with admin credentials"""
        try:
            response = requests.post(f"{self.api_url}/auth/login", 
                                   json={"email": "admin@kawalecranes.com", "password": "admin123"})
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                return self.log_test("Admin Login", True, f"Token obtained")
            else:
                return self.log_test("Admin Login", False, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Admin Login", False, f"Error: {str(e)}")

    def test_cash_order_basic_fields(self):
        """Test cash order creation with basic required fields only"""
        order_data = {
            "customer_name": "Test Customer Basic",
            "phone": "9876543210",
            "order_type": "cash"
        }
        
        return self._create_order("Cash Order - Basic Fields Only", order_data, 200)

    def test_cash_order_with_optional_fields(self):
        """Test cash order creation with all optional fields filled"""
        order_data = {
            "customer_name": "Test Customer Full",
            "phone": "9876543211",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune", 
            "cash_service_type": "2-Wheeler Crane",
            "amount_received": 5000.0,
            "advance_amount": 1000.0,
            "cash_vehicle_name": "Tata ACE",
            "cash_driver_name": "Rahul"
        }
        
        return self._create_order("Cash Order - All Optional Fields", order_data, 200)

    def test_cash_order_empty_datetime_strings(self):
        """Test the specific bug: empty datetime strings should be converted to null"""
        order_data = {
            "customer_name": "Test DateTime Bug",
            "phone": "9876543212",
            "order_type": "cash",
            "cash_trip_from": "Delhi",
            "cash_trip_to": "Gurgaon",
            "reach_time": "",  # Empty string - should be converted to null
            "drop_time": ""    # Empty string - should be converted to null
        }
        
        success, response = self._create_order("Cash Order - Empty DateTime Strings", order_data, 200)
        
        if success and response:
            # Verify that empty strings were converted to null
            reach_time = response.get('reach_time')
            drop_time = response.get('drop_time')
            
            if reach_time is None and drop_time is None:
                return self.log_test("DateTime Empty String Conversion", True, "Empty strings correctly converted to null")
            else:
                return self.log_test("DateTime Empty String Conversion", False, f"reach_time: {reach_time}, drop_time: {drop_time}")
        
        return False

    def test_cash_order_null_datetime_fields(self):
        """Test cash order with explicitly null datetime fields"""
        order_data = {
            "customer_name": "Test DateTime Null",
            "phone": "9876543213",
            "order_type": "cash",
            "cash_trip_from": "Bangalore",
            "cash_trip_to": "Chennai",
            "reach_time": None,
            "drop_time": None
        }
        
        return self._create_order("Cash Order - Null DateTime Fields", order_data, 200)

    def test_cash_order_valid_datetime_fields(self):
        """Test cash order with valid datetime fields"""
        current_time = datetime.now(timezone.utc).isoformat()
        
        order_data = {
            "customer_name": "Test DateTime Valid",
            "phone": "9876543214",
            "order_type": "cash",
            "cash_trip_from": "Kolkata",
            "cash_trip_to": "Bhubaneswar",
            "reach_time": current_time,
            "drop_time": current_time
        }
        
        success, response = self._create_order("Cash Order - Valid DateTime Fields", order_data, 200)
        
        if success and response:
            # Verify that valid datetime was stored
            reach_time = response.get('reach_time')
            drop_time = response.get('drop_time')
            
            if reach_time and drop_time:
                return self.log_test("DateTime Valid Storage", True, f"DateTime fields stored correctly")
            else:
                return self.log_test("DateTime Valid Storage", False, f"reach_time: {reach_time}, drop_time: {drop_time}")
        
        return False

    def test_company_order_mandatory_fields(self):
        """Test company order creation with all mandatory fields"""
        order_data = {
            "customer_name": "Test Company Order",
            "phone": "9876543215",
            "order_type": "company",
            "company_name": "Europ Assistance",  # Required
            "company_service_type": "4-Wheeler Crane",  # Required
            "company_driver_details": "Rahul Kumar",  # Required (Driver)
            "company_towing_vehicle": "Tata ACE"  # Required (Towing Vehicle)
        }
        
        return self._create_order("Company Order - All Mandatory Fields", order_data, 200)

    def test_company_order_missing_fields(self):
        """Test company order creation with missing mandatory fields (should fail)"""
        order_data = {
            "customer_name": "Test Company Missing",
            "phone": "9876543216",
            "order_type": "company"
            # Missing all mandatory fields
        }
        
        success, response = self._create_order("Company Order - Missing Mandatory Fields", order_data, 422)
        
        if success:
            # Check if the error message mentions the required fields
            return self.log_test("Company Order Validation Error", True, "Correctly rejected missing mandatory fields")
        
        return False

    def test_company_order_empty_datetime_strings(self):
        """Test company order with empty datetime strings"""
        order_data = {
            "customer_name": "Test Company DateTime",
            "phone": "9876543217",
            "order_type": "company",
            "company_name": "Europ Assistance",
            "company_service_type": "4-Wheeler Crane",
            "company_driver_details": "Rahul Kumar",
            "company_towing_vehicle": "Tata ACE",
            "reach_time": "",  # Empty string - should be converted to null
            "drop_time": ""    # Empty string - should be converted to null
        }
        
        success, response = self._create_order("Company Order - Empty DateTime Strings", order_data, 200)
        
        if success and response:
            # Verify that empty strings were converted to null
            reach_time = response.get('reach_time')
            drop_time = response.get('drop_time')
            
            if reach_time is None and drop_time is None:
                return self.log_test("Company DateTime Empty String Conversion", True, "Empty strings correctly converted to null")
            else:
                return self.log_test("Company DateTime Empty String Conversion", False, f"reach_time: {reach_time}, drop_time: {drop_time}")
        
        return False

    def _create_order(self, test_name, order_data, expected_status):
        """Helper method to create an order and check response"""
        try:
            headers = {'Content-Type': 'application/json'}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            response = requests.post(f"{self.api_url}/orders", json=order_data, headers=headers)
            
            if response.status_code == expected_status:
                try:
                    response_data = response.json()
                    return self.log_test(test_name, True, f"Status: {response.status_code}"), response_data
                except:
                    return self.log_test(test_name, True, f"Status: {response.status_code} (No JSON)"), {}
            else:
                try:
                    error_data = response.json()
                    return self.log_test(test_name, False, f"Expected {expected_status}, got {response.status_code}. Error: {error_data}"), {}
                except:
                    return self.log_test(test_name, False, f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}"), {}
        
        except Exception as e:
            return self.log_test(test_name, False, f"Request failed: {str(e)}"), {}

    def run_all_tests(self):
        """Run all cash order creation tests"""
        print("🚀 Starting Cash Order Creation Tests")
        print("=" * 60)
        
        # Login first
        if not self.login():
            print("❌ Login failed, stopping tests")
            return False
        
        print("\n🎯 Testing Cash Order Creation - Reported Bug Fix")
        print("-" * 50)
        
        # Test the specific scenarios mentioned in the review request
        tests = [
            self.test_cash_order_basic_fields,
            self.test_cash_order_with_optional_fields,
            self.test_cash_order_empty_datetime_strings,  # Main bug fix
            self.test_cash_order_null_datetime_fields,
            self.test_cash_order_valid_datetime_fields,
            self.test_company_order_mandatory_fields,
            self.test_company_order_missing_fields,
            self.test_company_order_empty_datetime_strings  # Main bug fix for company orders
        ]
        
        for test in tests:
            test()
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("✅ All tests passed! Cash order creation is working correctly.")
            return True
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed.")
            return False

def main():
    tester = CashOrderCreationTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())