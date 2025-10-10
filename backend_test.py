#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import uuid

class CraneOrderAPITester:
    def __init__(self, base_url="https://wheelerdata-entry.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_orders = []
        self.token = None

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        result = {
            "test_name": name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status} - {name}: {details}")
        return success

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication token if available
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_json = response.json()
                    details = f"Status: {response.status_code}"
                    return self.log_test(name, True, details, response_json), response_json
                except:
                    details = f"Status: {response.status_code} (No JSON response)"
                    return self.log_test(name, True, details), {}
            else:
                try:
                    error_data = response.json()
                    details = f"Expected {expected_status}, got {response.status_code}. Error: {error_data}"
                except:
                    details = f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}"
                return self.log_test(name, False, details), {}

        except requests.exceptions.RequestException as e:
            details = f"Request failed: {str(e)}"
            return self.log_test(name, False, details), {}

    def test_login(self):
        """Test admin login and get token"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@kawalecranes.com", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.log_test("Token Obtained", True, f"Token length: {len(self.token)}")
            return True
        return False

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_create_cash_order(self):
        """Test creating a cash order"""
        cash_order_data = {
            "customer_name": "John Doe",
            "phone": "9876543210",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune",
            "cash_vehicle_name": "Tata ACE",
            "cash_vehicle_number": "MH12AB1234",
            "cash_service_type": "2-Wheeler Crane",
            "amount_received": 5000.0,
            "advance_amount": 1000.0,
            "cash_kms_travelled": 150.0,
            "cash_toll": 200.0,
            "cash_diesel": 800.0,
            "cash_diesel_refill_location": "Highway Petrol Pump"
        }
        
        success, response = self.run_test("Create Cash Order", "POST", "orders", 200, cash_order_data)
        if success and response:
            self.created_orders.append(response.get('id'))
        return success, response

    def test_create_company_order(self):
        """Test creating a company order"""
        company_order_data = {
            "customer_name": "Jane Smith",
            "phone": "9876543211",
            "order_type": "company",
            "name_of_firm": "ABC Transport Ltd",
            "case_id_file_number": "CASE001",
            "company_trip_from": "Delhi",
            "company_trip_to": "Gurgaon",
            "company_vehicle_name": "Mahindra Bolero",
            "company_vehicle_number": "DL01CD5678",
            "company_service_type": "4-Wheeler Crane",
            "company_kms_travelled": 50.0,
            "company_toll": 100.0,
            "company_diesel": 400.0,
            "diesel_name": "HP Diesel",
            "company_diesel_refill_location": "City Petrol Station"
        }
        
        success, response = self.run_test("Create Company Order", "POST", "orders", 200, company_order_data)
        if success and response:
            self.created_orders.append(response.get('id'))
        return success, response

    def test_get_all_orders(self):
        """Test getting all orders"""
        return self.run_test("Get All Orders", "GET", "orders", 200)

    def test_get_orders_with_filters(self):
        """Test getting orders with filters"""
        # Test filter by order type
        success1, _ = self.run_test("Filter by Cash Orders", "GET", "orders", 200, params={"order_type": "cash"})
        success2, _ = self.run_test("Filter by Company Orders", "GET", "orders", 200, params={"order_type": "company"})
        
        # Test filter by customer name
        success3, _ = self.run_test("Filter by Customer Name", "GET", "orders", 200, params={"customer_name": "John"})
        
        # Test filter by phone
        success4, _ = self.run_test("Filter by Phone", "GET", "orders", 200, params={"phone": "9876543210"})
        
        return success1 and success2 and success3 and success4

    def test_get_single_order(self):
        """Test getting a single order by ID"""
        if not self.created_orders:
            return self.log_test("Get Single Order", False, "No orders created to test with")
        
        order_id = self.created_orders[0]
        return self.run_test("Get Single Order", "GET", f"orders/{order_id}", 200)

    def test_update_order(self):
        """Test updating an order"""
        if not self.created_orders:
            return self.log_test("Update Order", False, "No orders created to test with")
        
        order_id = self.created_orders[0]
        update_data = {
            "customer_name": "John Doe Updated",
            "phone": "9876543299"
        }
        
        return self.run_test("Update Order", "PUT", f"orders/{order_id}", 200, update_data)

    def test_delete_order(self):
        """Test deleting an order"""
        if not self.created_orders:
            return self.log_test("Delete Order", False, "No orders created to test with")
        
        order_id = self.created_orders[-1]  # Delete the last created order
        success, _ = self.run_test("Delete Order", "DELETE", f"orders/{order_id}", 200)
        if success:
            self.created_orders.remove(order_id)
        return success

    def test_get_stats_summary(self):
        """Test getting order statistics"""
        return self.run_test("Get Order Statistics", "GET", "orders/stats/summary", 200)

    def test_invalid_endpoints(self):
        """Test invalid endpoints and error handling"""
        # Test non-existent order
        success1, _ = self.run_test("Get Non-existent Order", "GET", "orders/invalid-id", 404)
        
        # Test invalid order creation (missing required fields)
        invalid_data = {"customer_name": "Test"}  # Missing phone and order_type
        success2, _ = self.run_test("Create Invalid Order", "POST", "orders", 422, invalid_data)
        
        return success1 and success2

    def test_cash_order_with_driver_dropdown(self):
        """Test creating cash order with driver dropdown field"""
        order_data = {
            "customer_name": "Test Driver Cash",
            "phone": "9876543220",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune",
            "cash_vehicle_name": "Tata ACE",
            "cash_service_type": "2-Wheeler Crane",
            "amount_received": 5000.0,
            "cash_driver_name": "Rahul"  # Testing driver dropdown
        }
        
        success, response = self.run_test("Create Cash Order with Driver", "POST", "orders", 201, order_data)
        
        if success and 'id' in response:
            self.created_orders.append(response['id'])
            # Verify driver name is stored correctly
            if response.get('cash_driver_name') == 'Rahul':
                self.log_test("Cash Driver Field Verification", True, f"Driver stored: {response['cash_driver_name']}")
                return True
            else:
                self.log_test("Cash Driver Field Verification", False, f"Expected: Rahul, Got: {response.get('cash_driver_name')}")
        return False

    def test_company_order_with_dropdowns(self):
        """Test creating company order with all new dropdown fields"""
        order_data = {
            "customer_name": "Test Company Dropdowns",
            "phone": "9876543221",
            "order_type": "company",
            "name_of_firm": "Kawale Cranes",  # Testing firm dropdown
            "company_name": "Mondial",  # Testing company dropdown
            "case_id_file_number": "CASE123",
            "company_trip_from": "Delhi",
            "company_trip_to": "Gurgaon",
            "company_vehicle_name": "Mahindra Bolero",
            "company_service_type": "4-Wheeler Crane",
            "company_driver_name": "Subhash"  # Testing driver dropdown
        }
        
        success, response = self.run_test("Create Company Order with Dropdowns", "POST", "orders", 201, order_data)
        
        if success and 'id' in response:
            self.created_orders.append(response['id'])
            # Verify all dropdown values are stored correctly
            checks = [
                ('name_of_firm', 'Kawale Cranes'),
                ('company_name', 'Mondial'),
                ('company_driver_name', 'Subhash')
            ]
            
            all_correct = True
            for field, expected in checks:
                actual = response.get(field)
                if actual == expected:
                    self.log_test(f"Company {field} Verification", True, f"{field}: {actual}")
                else:
                    self.log_test(f"Company {field} Verification", False, f"Expected: {expected}, Got: {actual}")
                    all_correct = False
            
            return all_correct
        return False

    def test_all_driver_options(self):
        """Test creating orders with different driver options"""
        driver_options = ["Rahul", "Subhash", "Dubey", "Sudhir", "Vikas"]
        
        success_count = 0
        for i, driver in enumerate(driver_options):
            order_data = {
                "customer_name": f"Driver Test {driver}",
                "phone": f"987654322{i}",
                "order_type": "cash",
                "cash_driver_name": driver,
                "cash_vehicle_name": "Test Vehicle",
                "amount_received": 1000.0
            }
            
            success, response = self.run_test(f"Create Order with Driver {driver}", "POST", "orders", 201, order_data)
            
            if success and 'id' in response:
                self.created_orders.append(response['id'])
                if response.get('cash_driver_name') == driver:
                    success_count += 1
                    
        return success_count == len(driver_options)

    def test_all_firm_options(self):
        """Test creating orders with different firm options"""
        firm_options = ["Kawale Cranes", "Vira Towing", "Sarang Cranes", "Vidharbha Towing"]
        
        success_count = 0
        for i, firm in enumerate(firm_options):
            order_data = {
                "customer_name": f"Firm Test {firm}",
                "phone": f"987654323{i}",
                "order_type": "company",
                "name_of_firm": firm,
                "company_name": "Mondial",
                "case_id_file_number": f"FIRM{i}"
            }
            
            success, response = self.run_test(f"Create Order with Firm {firm}", "POST", "orders", 201, order_data)
            
            if success and 'id' in response:
                self.created_orders.append(response['id'])
                if response.get('name_of_firm') == firm:
                    success_count += 1
                    
        return success_count == len(firm_options)

    def test_all_company_options(self):
        """Test creating orders with different company options"""
        company_options = ["Mondial", "TVS", "Europ Assistance"]
        
        success_count = 0
        for i, company in enumerate(company_options):
            order_data = {
                "customer_name": f"Company Test {company}",
                "phone": f"987654324{i}",
                "order_type": "company",
                "name_of_firm": "Kawale Cranes",
                "company_name": company,
                "case_id_file_number": f"COMP{i}"
            }
            
            success, response = self.run_test(f"Create Order with Company {company}", "POST", "orders", 201, order_data)
            
            if success and 'id' in response:
                self.created_orders.append(response['id'])
                if response.get('company_name') == company:
                    success_count += 1
                    
        return success_count == len(company_options)

    def cleanup_created_orders(self):
        """Clean up any remaining test orders"""
        print("\n🧹 Cleaning up test orders...")
        for order_id in self.created_orders[:]:
            try:
                response = requests.delete(f"{self.api_url}/orders/{order_id}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ Cleaned up order: {order_id}")
                    self.created_orders.remove(order_id)
                else:
                    print(f"⚠️ Failed to cleanup order: {order_id}")
            except Exception as e:
                print(f"⚠️ Error cleaning up order {order_id}: {str(e)}")

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Crane Orders API Tests")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 60)

        # Test sequence
        test_methods = [
            self.test_root_endpoint,
            self.test_create_cash_order,
            self.test_create_company_order,
            self.test_get_all_orders,
            self.test_get_orders_with_filters,
            self.test_get_single_order,
            self.test_update_order,
            self.test_get_stats_summary,
            self.test_delete_order,
            self.test_invalid_endpoints
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Test execution error: {str(e)}")
            print()

        # Cleanup
        self.cleanup_created_orders()

        # Print summary
        print("=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['details']}")
            return 1

def main():
    """Main test execution"""
    tester = CraneOrderAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())