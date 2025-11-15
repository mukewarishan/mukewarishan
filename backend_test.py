#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import uuid

class CraneOrderAPITester:
    def __init__(self, base_url="https://fleet-command-28.preview.emergentagent.com"):
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
            "company_name": "Europ Assistance",  # Required field
            "case_id_file_number": "CASE001",
            "company_trip_from": "Delhi",
            "company_trip_to": "Gurgaon",
            "company_vehicle_name": "Mahindra Bolero",
            "company_vehicle_number": "DL01CD5678",
            "company_service_type": "4-Wheeler Crane",  # Required field
            "company_driver_details": "Rahul Kumar",  # Required field (Driver)
            "company_towing_vehicle": "Tata ACE",  # Required field (Towing Vehicle)
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

    def test_user_management_endpoints(self):
        """Test user management CRUD operations (Super Admin functionality)"""
        print("\n🔐 Testing User Management Endpoints...")
        
        # Test get all users
        success1, users_response = self.run_test("Get All Users", "GET", "users", 200)
        
        # Test create new user
        new_user_data = {
            "email": "testuser@kawalecranes.com",
            "full_name": "Test User",
            "password": "testpass123",
            "role": "data_entry"
        }
        success2, create_response = self.run_test("Create New User", "POST", "auth/register", 200, new_user_data)
        
        created_user_id = None
        if success2 and create_response:
            created_user_id = create_response.get('id')
        
        # Test update user
        success3 = True
        if created_user_id:
            update_data = {
                "full_name": "Updated Test User",
                "role": "admin"
            }
            success3, _ = self.run_test("Update User", "PUT", f"users/{created_user_id}", 200, update_data)
        
        # Test delete user
        success4 = True
        if created_user_id:
            success4, _ = self.run_test("Delete User", "DELETE", f"users/{created_user_id}", 200)
        
        return success1 and success2 and success3 and success4

    def test_authentication_system(self):
        """Test authentication system comprehensively"""
        print("\n🔐 Testing Authentication System...")
        
        # Test login with admin credentials
        success1, login_response = self.run_test(
            "Admin Login Test",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@kawalecranes.com", "password": "admin123"}
        )
        
        # Verify JWT token functionality
        success2 = False
        if success1 and 'access_token' in login_response:
            token = login_response['access_token']
            # Test using token for authenticated endpoint
            old_token = self.token
            self.token = token
            success2, _ = self.run_test("JWT Token Verification", "GET", "auth/me", 200)
            self.token = old_token
        
        # Test logout
        success3, _ = self.run_test("User Logout", "POST", "auth/logout", 200)
        
        # Test invalid login
        success4, _ = self.run_test(
            "Invalid Login Test",
            "POST", 
            "auth/login",
            401,
            data={"email": "admin@kawalecranes.com", "password": "wrongpassword"}
        )
        
        return success1 and success2 and success3 and success4

    def test_role_based_access_control(self):
        """Test role-based access control"""
        print("\n🛡️ Testing Role-Based Access Control...")
        
        # Create a data entry user for testing
        data_entry_user = {
            "email": "dataentry@kawalecranes.com",
            "full_name": "Data Entry User",
            "password": "dataentry123",
            "role": "data_entry"
        }
        
        success1, create_response = self.run_test("Create Data Entry User", "POST", "auth/register", 200, data_entry_user)
        
        # Login as data entry user
        success2, login_response = self.run_test(
            "Data Entry Login",
            "POST",
            "auth/login", 
            200,
            data={"email": "dataentry@kawalecranes.com", "password": "dataentry123"}
        )
        
        # Test data entry user trying to access admin-only endpoints
        success3 = False
        if success2 and 'access_token' in login_response:
            old_token = self.token
            self.token = login_response['access_token']
            
            # Data entry user should NOT be able to delete orders (admin only)
            if self.created_orders:
                success3, _ = self.run_test("Data Entry Delete Order (Should Fail)", "DELETE", f"orders/{self.created_orders[0]}", 403)
            
            # Data entry user should NOT be able to access user management
            success4, _ = self.run_test("Data Entry Get Users (Should Fail)", "GET", "users", 403)
            
            self.token = old_token
            success3 = success3 and success4
        
        # Cleanup - delete the test user
        if create_response and 'id' in create_response:
            self.run_test("Cleanup Data Entry User", "DELETE", f"users/{create_response['id']}", 200)
        
        return success1 and success2 and success3

    def test_export_endpoints(self):
        """Test PDF and Excel export endpoints"""
        print("\n📄 Testing Export Endpoints...")
        
        # Test PDF export
        success1, pdf_response = self.run_test("PDF Export", "GET", "export/pdf", 200)
        
        # Test Excel export  
        success2, excel_response = self.run_test("Excel Export", "GET", "export/excel", 200)
        
        # Test Google Sheets export (should return 404 Not Found after removal)
        success3, sheets_response = self.run_test("Google Sheets Export (Should be 404)", "GET", "export/googlesheets", 404)
        
        # Test export with filters
        success4, _ = self.run_test("PDF Export with Filters", "GET", "export/pdf", 200, params={"order_type": "cash", "limit": 10})
        success5, _ = self.run_test("Excel Export with Filters", "GET", "export/excel", 200, params={"order_type": "company", "limit": 10})
        
        return success1 and success2 and success3 and success4 and success5

    def test_google_sheets_removal_verification(self):
        """Comprehensive test to verify Google Sheets functionality has been completely removed"""
        print("\n🗑️ Testing Google Sheets Removal Verification...")
        
        # Test 1: Google Sheets endpoint should return 404 Not Found
        success1, response1 = self.run_test("Google Sheets Endpoint Removal", "GET", "export/googlesheets", 404)
        
        # Test 2: Verify no Google Sheets related imports cause errors
        # This is tested implicitly by the server running without import errors
        
        # Test 3: Verify Excel export still works (should not be affected)
        success2, response2 = self.run_test("Excel Export Still Works", "GET", "export/excel", 200)
        
        # Test 4: Verify PDF export still works (should not be affected)  
        success3, response3 = self.run_test("PDF Export Still Works", "GET", "export/pdf", 200)
        
        # Test 5: Verify basic CRUD operations still work (no import errors)
        test_order = {
            "customer_name": "Google Sheets Removal Test",
            "phone": "9876543999",
            "order_type": "cash",
            "cash_vehicle_name": "Test Vehicle",
            "amount_received": 1000.0
        }
        
        success4, response4 = self.run_test("CRUD Still Works After Removal", "POST", "orders", 200, test_order)
        if success4 and 'id' in response4:
            self.created_orders.append(response4['id'])
        
        # Overall verification
        all_passed = success1 and success2 and success3 and success4
        
        if all_passed:
            self.log_test("Google Sheets Removal Complete", True, "✅ Google Sheets functionality completely removed, other features intact")
        else:
            failed_tests = []
            if not success1: failed_tests.append("Endpoint still exists")
            if not success2: failed_tests.append("Excel export broken")
            if not success3: failed_tests.append("PDF export broken")
            if not success4: failed_tests.append("CRUD operations broken")
            
            self.log_test("Google Sheets Removal Complete", False, f"❌ Issues found: {', '.join(failed_tests)}")
        
        return all_passed

    def test_audit_logging(self):
        """Test audit logging functionality"""
        print("\n📋 Testing Audit Logging...")
        
        # Test get audit logs
        success1, audit_response = self.run_test("Get Audit Logs", "GET", "audit-logs", 200)
        
        # Test audit logs with filters
        success2, _ = self.run_test("Filter Audit Logs by Action", "GET", "audit-logs", 200, params={"action": "LOGIN"})
        success3, _ = self.run_test("Filter Audit Logs by Resource", "GET", "audit-logs", 200, params={"resource_type": "ORDER"})
        success4, _ = self.run_test("Filter Audit Logs by User", "GET", "audit-logs", 200, params={"user_email": "admin"})
        
        # Verify audit logs contain expected entries
        success5 = False
        if success1 and audit_response:
            logs = audit_response if isinstance(audit_response, list) else []
            # Check if we have some audit logs
            if len(logs) > 0:
                success5 = True
                self.log_test("Audit Logs Content Verification", True, f"Found {len(logs)} audit log entries")
            else:
                self.log_test("Audit Logs Content Verification", False, "No audit logs found")
        
        return success1 and success2 and success3 and success4 and success5

    def test_mongodb_connections(self):
        """Test MongoDB connections and data retrieval"""
        print("\n🗄️ Testing MongoDB Connections...")
        
        # Test basic data retrieval (orders)
        success1, orders_response = self.run_test("MongoDB Orders Retrieval", "GET", "orders", 200)
        
        # Test data persistence by creating and retrieving an order
        test_order = {
            "customer_name": "MongoDB Test User",
            "phone": "9876543299",
            "order_type": "cash",
            "cash_vehicle_name": "Test Vehicle",
            "amount_received": 1000.0
        }
        
        success2, create_response = self.run_test("MongoDB Data Persistence Test", "POST", "orders", 200, test_order)
        
        success3 = False
        if success2 and create_response and 'id' in create_response:
            order_id = create_response['id']
            self.created_orders.append(order_id)
            
            # Retrieve the created order to verify persistence
            success3, retrieve_response = self.run_test("MongoDB Data Retrieval Test", "GET", f"orders/{order_id}", 200)
            
            if success3 and retrieve_response:
                # Verify data integrity
                if (retrieve_response.get('customer_name') == test_order['customer_name'] and
                    retrieve_response.get('phone') == test_order['phone']):
                    self.log_test("MongoDB Data Integrity", True, "Data stored and retrieved correctly")
                else:
                    self.log_test("MongoDB Data Integrity", False, "Data mismatch after storage/retrieval")
        
        return success1 and success2 and success3

    def test_filtering_functionality(self):
        """Test filtering functionality in orders endpoint"""
        print("\n🔍 Testing Filtering Functionality...")
        
        # Create test orders with specific data for filtering
        cash_order = {
            "customer_name": "Filter Test Cash User",
            "phone": "9876543280",
            "order_type": "cash",
            "cash_vehicle_name": "Filter Test Vehicle",
            "amount_received": 2000.0
        }
        
        company_order = {
            "customer_name": "Filter Test Company User", 
            "phone": "9876543281",
            "order_type": "company",
            "name_of_firm": "Filter Test Firm",
            "company_name": "Filter Test Company",
            "case_id_file_number": "FILTER001"
        }
        
        # Create the test orders
        success1, cash_response = self.run_test("Create Cash Order for Filter Test", "POST", "orders", 200, cash_order)
        success2, company_response = self.run_test("Create Company Order for Filter Test", "POST", "orders", 200, company_order)
        
        if success1 and cash_response and 'id' in cash_response:
            self.created_orders.append(cash_response['id'])
        if success2 and company_response and 'id' in company_response:
            self.created_orders.append(company_response['id'])
        
        # Test various filters
        success3, _ = self.run_test("Filter by Order Type (Cash)", "GET", "orders", 200, params={"order_type": "cash"})
        success4, _ = self.run_test("Filter by Order Type (Company)", "GET", "orders", 200, params={"order_type": "company"})
        success5, _ = self.run_test("Filter by Customer Name", "GET", "orders", 200, params={"customer_name": "Filter Test"})
        success6, _ = self.run_test("Filter by Phone Number", "GET", "orders", 200, params={"phone": "9876543280"})
        
        # Test pagination
        success7, _ = self.run_test("Pagination Test (Limit)", "GET", "orders", 200, params={"limit": 5})
        success8, _ = self.run_test("Pagination Test (Skip)", "GET", "orders", 200, params={"skip": 2, "limit": 3})
        
        return success1 and success2 and success3 and success4 and success5 and success6 and success7 and success8

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

    def test_care_off_fields_cash_order(self):
        """Test Care Off fields in cash orders"""
        # Test with both Care Off fields filled
        order_data = {
            "customer_name": "Care Off Test User",
            "phone": "9876543250",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune",
            "cash_vehicle_name": "Tata ACE",
            "cash_service_type": "2-Wheeler Crane",
            "amount_received": 5000.0,
            "advance_amount": 1000.0,
            "care_off": "Special discount for regular customer",
            "care_off_amount": 500.0
        }
        
        success, response = self.run_test("Create Cash Order with Care Off Fields", "POST", "orders", 201, order_data)
        
        if success and 'id' in response:
            self.created_orders.append(response['id'])
            # Verify Care Off fields are stored correctly
            care_off_correct = response.get('care_off') == "Special discount for regular customer"
            care_off_amount_correct = response.get('care_off_amount') == 500.0
            
            if care_off_correct and care_off_amount_correct:
                self.log_test("Care Off Fields Verification", True, f"Care Off: {response['care_off']}, Amount: {response['care_off_amount']}")
                return True
            else:
                self.log_test("Care Off Fields Verification", False, f"Care Off: {response.get('care_off')}, Amount: {response.get('care_off_amount')}")
        return False

    def test_care_off_fields_optional(self):
        """Test that Care Off fields are optional in cash orders"""
        # Test cash order without Care Off fields
        order_data = {
            "customer_name": "No Care Off Test",
            "phone": "9876543251",
            "order_type": "cash",
            "cash_trip_from": "Delhi",
            "cash_trip_to": "Gurgaon",
            "cash_vehicle_name": "Mahindra Bolero",
            "amount_received": 3000.0
        }
        
        success, response = self.run_test("Create Cash Order without Care Off Fields", "POST", "orders", 201, order_data)
        
        if success and 'id' in response:
            self.created_orders.append(response['id'])
            # Verify Care Off fields are null/empty when not provided
            care_off_null = response.get('care_off') is None
            care_off_amount_null = response.get('care_off_amount') is None
            
            if care_off_null and care_off_amount_null:
                self.log_test("Care Off Fields Optional Verification", True, "Care Off fields correctly null when not provided")
                return True
            else:
                self.log_test("Care Off Fields Optional Verification", False, f"Care Off: {response.get('care_off')}, Amount: {response.get('care_off_amount')}")
        return False

    def test_care_off_fields_company_order(self):
        """Test that Care Off fields work in company orders (backend should accept them)"""
        # Test company order with Care Off fields (backend should accept but frontend shouldn't show)
        order_data = {
            "customer_name": "Company Care Off Test",
            "phone": "9876543252",
            "order_type": "company",
            "name_of_firm": "Kawale Cranes",
            "company_name": "Mondial",
            "case_id_file_number": "CARE001",
            "company_trip_from": "Mumbai",
            "company_trip_to": "Pune",
            "care_off": "Company discount",
            "care_off_amount": 300.0
        }
        
        success, response = self.run_test("Create Company Order with Care Off Fields", "POST", "orders", 201, order_data)
        
        if success and 'id' in response:
            self.created_orders.append(response['id'])
            # Backend should accept Care Off fields even for company orders
            care_off_stored = response.get('care_off') == "Company discount"
            care_off_amount_stored = response.get('care_off_amount') == 300.0
            
            if care_off_stored and care_off_amount_stored:
                self.log_test("Company Order Care Off Backend Storage", True, "Backend accepts Care Off fields for company orders")
                return True
            else:
                self.log_test("Company Order Care Off Backend Storage", False, f"Care Off: {response.get('care_off')}, Amount: {response.get('care_off_amount')}")
        return False

    def test_care_off_amount_validation(self):
        """Test Care Off amount field validation"""
        # Test with invalid amount (string instead of number)
        order_data = {
            "customer_name": "Invalid Care Off Amount",
            "phone": "9876543253",
            "order_type": "cash",
            "cash_vehicle_name": "Test Vehicle",
            "care_off": "Test discount",
            "care_off_amount": "invalid_amount"  # Should be a number
        }
        
        # This should fail validation (422 Unprocessable Entity)
        success, response = self.run_test("Create Order with Invalid Care Off Amount", "POST", "orders", 422, order_data)
        return success

    def test_update_order_with_care_off(self):
        """Test updating an existing order with Care Off fields"""
        if not self.created_orders:
            return self.log_test("Update Order with Care Off", False, "No orders created to test with")
        
        order_id = self.created_orders[0]
        update_data = {
            "care_off": "Updated care off reason",
            "care_off_amount": 750.0
        }
        
        success, response = self.run_test("Update Order with Care Off Fields", "PUT", f"orders/{order_id}", 200, update_data)
        
        if success and response:
            # Verify the update worked
            care_off_updated = response.get('care_off') == "Updated care off reason"
            care_off_amount_updated = response.get('care_off_amount') == 750.0
            
            if care_off_updated and care_off_amount_updated:
                self.log_test("Care Off Update Verification", True, "Care Off fields updated successfully")
                return True
            else:
                self.log_test("Care Off Update Verification", False, f"Care Off: {response.get('care_off')}, Amount: {response.get('care_off_amount')}")
        return False

    def test_incentive_fields_admin_only(self):
        """Test incentive fields for admin users"""
        # Test creating order with incentive fields (admin only)
        order_data = {
            "customer_name": "Incentive Test User",
            "phone": "9876543260",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune",
            "cash_vehicle_name": "Tata ACE",
            "amount_received": 5000.0,
            "incentive_amount": 500.0,
            "incentive_reason": "Excellent service and quick delivery"
        }
        
        success, response = self.run_test("Create Order with Incentive Fields", "POST", "orders", 200, order_data)
        
        if success and 'id' in response:
            self.created_orders.append(response['id'])
            # Verify incentive fields are stored correctly
            incentive_amount_correct = response.get('incentive_amount') == 500.0
            incentive_reason_correct = response.get('incentive_reason') == "Excellent service and quick delivery"
            
            if incentive_amount_correct and incentive_reason_correct:
                self.log_test("Incentive Fields Verification", True, f"Amount: {response['incentive_amount']}, Reason: {response['incentive_reason']}")
                return True
            else:
                self.log_test("Incentive Fields Verification", False, f"Amount: {response.get('incentive_amount')}, Reason: {response.get('incentive_reason')}")
        return False

    def test_incentive_fields_optional(self):
        """Test that incentive fields are optional"""
        order_data = {
            "customer_name": "No Incentive Test",
            "phone": "9876543261",
            "order_type": "company",
            "name_of_firm": "Kawale Cranes",
            "company_name": "Mondial",
            "case_id_file_number": "NOINC001"
        }
        
        success, response = self.run_test("Create Order without Incentive Fields", "POST", "orders", 200, order_data)
        
        if success and 'id' in response:
            self.created_orders.append(response['id'])
            # Verify incentive fields are null when not provided
            incentive_amount_null = response.get('incentive_amount') is None
            incentive_reason_null = response.get('incentive_reason') is None
            
            if incentive_amount_null and incentive_reason_null:
                self.log_test("Incentive Fields Optional Verification", True, "Incentive fields correctly null when not provided")
                return True
            else:
                self.log_test("Incentive Fields Optional Verification", False, f"Amount: {response.get('incentive_amount')}, Reason: {response.get('incentive_reason')}")
        return False

    def test_reach_drop_time_company_orders(self):
        """Test reach and drop time fields for company orders"""
        from datetime import datetime, timezone
        
        reach_time = datetime.now(timezone.utc).isoformat()
        drop_time = datetime.now(timezone.utc).isoformat()
        
        order_data = {
            "customer_name": "Reach Drop Time Test",
            "phone": "9876543262",
            "order_type": "company",
            "name_of_firm": "Kawale Cranes",
            "company_name": "Mondial",
            "case_id_file_number": "TIME001",
            "company_trip_from": "Delhi",
            "company_trip_to": "Gurgaon",
            "reach_time": reach_time,
            "drop_time": drop_time
        }
        
        success, response = self.run_test("Create Company Order with Reach/Drop Time", "POST", "orders", 200, order_data)
        
        if success and 'id' in response:
            self.created_orders.append(response['id'])
            # Verify reach and drop time fields are stored
            reach_time_stored = response.get('reach_time') is not None
            drop_time_stored = response.get('drop_time') is not None
            
            if reach_time_stored and drop_time_stored:
                self.log_test("Reach/Drop Time Fields Verification", True, f"Reach: {response.get('reach_time')}, Drop: {response.get('drop_time')}")
                return True
            else:
                self.log_test("Reach/Drop Time Fields Verification", False, f"Reach: {response.get('reach_time')}, Drop: {response.get('drop_time')}")
        return False

    def test_bulk_delete_multiple_orders(self):
        """Test bulk delete functionality by creating and deleting multiple orders"""
        # Create multiple test orders for bulk delete
        bulk_order_ids = []
        
        for i in range(3):
            order_data = {
                "customer_name": f"Bulk Delete Test {i+1}",
                "phone": f"987654326{i+3}",
                "order_type": "cash",
                "cash_vehicle_name": f"Test Vehicle {i+1}",
                "amount_received": 1000.0 * (i+1)
            }
            
            success, response = self.run_test(f"Create Bulk Delete Test Order {i+1}", "POST", "orders", 200, order_data)
            
            if success and 'id' in response:
                bulk_order_ids.append(response['id'])
                self.created_orders.append(response['id'])
        
        # Now test deleting them one by one (simulating bulk delete)
        deleted_count = 0
        for order_id in bulk_order_ids:
            success, _ = self.run_test(f"Delete Order {order_id[:8]}", "DELETE", f"orders/{order_id}", 200)
            if success:
                deleted_count += 1
                if order_id in self.created_orders:
                    self.created_orders.remove(order_id)
        
        if deleted_count == len(bulk_order_ids):
            self.log_test("Bulk Delete Simulation", True, f"Successfully deleted {deleted_count} orders")
            return True
        else:
            self.log_test("Bulk Delete Simulation", False, f"Only deleted {deleted_count} out of {len(bulk_order_ids)} orders")
            return False

    def test_update_order_with_incentive(self):
        """Test updating an existing order with incentive fields"""
        if not self.created_orders:
            return self.log_test("Update Order with Incentive", False, "No orders created to test with")
        
        order_id = self.created_orders[0]
        update_data = {
            "incentive_amount": 750.0,
            "incentive_reason": "Updated incentive for exceptional performance"
        }
        
        success, response = self.run_test("Update Order with Incentive Fields", "PUT", f"orders/{order_id}", 200, update_data)
        
        if success and response:
            # Verify the update worked
            incentive_amount_updated = response.get('incentive_amount') == 750.0
            incentive_reason_updated = response.get('incentive_reason') == "Updated incentive for exceptional performance"
            
            if incentive_amount_updated and incentive_reason_updated:
                self.log_test("Incentive Update Verification", True, "Incentive fields updated successfully")
                return True
            else:
                self.log_test("Incentive Update Verification", False, f"Amount: {response.get('incentive_amount')}, Reason: {response.get('incentive_reason')}")
        return False

    def test_mixed_order_types_with_features(self):
        """Test creating orders with all new features combined"""
        # Cash order with incentive and care off
        cash_order = {
            "customer_name": "Mixed Features Cash",
            "phone": "9876543270",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune",
            "cash_vehicle_name": "Tata ACE",
            "amount_received": 5000.0,
            "care_off": "Regular customer discount",
            "care_off_amount": 200.0,
            "incentive_amount": 300.0,
            "incentive_reason": "Quick response time"
        }
        
        success1, response1 = self.run_test("Create Cash Order with All Features", "POST", "orders", 200, cash_order)
        if success1 and 'id' in response1:
            self.created_orders.append(response1['id'])
        
        # Company order with incentive and reach/drop times
        from datetime import datetime, timezone
        company_order = {
            "customer_name": "Mixed Features Company",
            "phone": "9876543271",
            "order_type": "company",
            "name_of_firm": "Kawale Cranes",
            "company_name": "Mondial",
            "case_id_file_number": "MIX001",
            "company_trip_from": "Delhi",
            "company_trip_to": "Gurgaon",
            "reach_time": datetime.now(timezone.utc).isoformat(),
            "drop_time": datetime.now(timezone.utc).isoformat(),
            "incentive_amount": 400.0,
            "incentive_reason": "Handled complex case efficiently"
        }
        
        success2, response2 = self.run_test("Create Company Order with All Features", "POST", "orders", 200, company_order)
        if success2 and 'id' in response2:
            self.created_orders.append(response2['id'])
        
        return success1 and success2

    def test_excel_import_datetime_fix(self):
        """CRITICAL TEST: Excel Import Date-Time Fix with User's File"""
        print("\n📥 CRITICAL PRIORITY: Testing Excel Import Date-Time Fix...")
        
        # Step 1: Get current order count before import
        success1, orders_before = self.run_test("Get Orders Count Before Import", "GET", "orders/stats/summary", 200)
        if not success1:
            return self.log_test("Excel Import DateTime Fix", False, "Failed to get initial order count")
        
        initial_count = orders_before.get('total_orders', 0)
        self.log_test("Initial Order Count", True, f"Found {initial_count} orders before import")
        
        # Step 2: Import the user's Excel file (15-11.xlsx)
        import os
        excel_file_path = "/app/15-11.xlsx"
        
        if not os.path.exists(excel_file_path):
            return self.log_test("Excel Import DateTime Fix", False, "User's Excel file (15-11.xlsx) not found")
        
        # Prepare file upload
        url = f"{self.api_url}/import/excel"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            with open(excel_file_path, 'rb') as f:
                files = {'file': ('15-11.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                response = requests.post(url, files=files, headers=headers, timeout=30)
            
            if response.status_code == 200:
                import_result = response.json()
                self.log_test("Excel File Import", True, f"Import successful: {import_result}")
                
                # Step 3: Verify import succeeded with success message
                if 'message' in import_result and 'success' in import_result['message'].lower():
                    self.log_test("Import Success Message", True, f"Success message: {import_result['message']}")
                else:
                    self.log_test("Import Success Message", False, f"Unexpected response: {import_result}")
                
                # Step 4: Check that new orders were added
                success4, orders_after = self.run_test("Get Orders Count After Import", "GET", "orders/stats/summary", 200)
                if success4:
                    final_count = orders_after.get('total_orders', 0)
                    imported_count = final_count - initial_count
                    
                    if imported_count > 0:
                        self.log_test("New Orders Added", True, f"Added {imported_count} new orders (from {initial_count} to {final_count})")
                        
                        # Step 5: CRITICAL - Verify date-time values from Excel file, NOT current date
                        success5, recent_orders = self.run_test("Get Recent Orders for DateTime Check", "GET", "orders", 200, params={"limit": imported_count + 5})
                        
                        if success5 and recent_orders:
                            # Look for orders with September 2025 dates (from Excel file)
                            september_2025_orders = []
                            current_date_orders = []
                            
                            for order in recent_orders:
                                order_date = order.get('date_time', '')
                                if '2025-09' in order_date:  # September 2025 from Excel
                                    september_2025_orders.append(order)
                                elif '2025-11-15' in order_date:  # Current date (would indicate bug)
                                    current_date_orders.append(order)
                            
                            # Verify we have orders with Excel dates, not current dates
                            if len(september_2025_orders) >= 3:  # Should have multiple orders from Excel
                                self.log_test("Excel DateTime Values Used", True, f"Found {len(september_2025_orders)} orders with September 2025 dates from Excel file")
                                
                                # Check specific sample records from Excel
                                sachi_order = next((o for o in september_2025_orders if 'Sachi' in o.get('customer_name', '')), None)
                                kartik_order = next((o for o in september_2025_orders if 'Kartik' in o.get('customer_name', '')), None)
                                
                                if sachi_order:
                                    sachi_date = sachi_order.get('date_time', '')
                                    if '2025-09-23' in sachi_date and '18:15' in sachi_date:
                                        self.log_test("Sachi Order DateTime Correct", True, f"Sachi order has correct Excel date: {sachi_date}")
                                    else:
                                        self.log_test("Sachi Order DateTime Correct", False, f"Sachi order date incorrect: {sachi_date}")
                                
                                if kartik_order:
                                    kartik_date = kartik_order.get('date_time', '')
                                    if '2025-09-23' in kartik_date and '10:26' in kartik_date:
                                        self.log_test("Kartik Order DateTime Correct", True, f"Kartik order has correct Excel date: {kartik_date}")
                                    else:
                                        self.log_test("Kartik Order DateTime Correct", False, f"Kartik order date incorrect: {kartik_date}")
                                
                                # Verify NO orders have current date (would indicate the bug still exists)
                                if len(current_date_orders) == 0:
                                    self.log_test("No Current Date Orders", True, "✅ No orders found with current date - fix working correctly")
                                    return True
                                else:
                                    self.log_test("No Current Date Orders", False, f"❌ Found {len(current_date_orders)} orders with current date - bug still exists")
                                    return False
                            else:
                                self.log_test("Excel DateTime Values Used", False, f"Only found {len(september_2025_orders)} orders with Excel dates, expected more")
                                return False
                        else:
                            self.log_test("Get Recent Orders for DateTime Check", False, "Failed to retrieve orders for date verification")
                            return False
                    else:
                        self.log_test("New Orders Added", False, f"No new orders added. Count remained {final_count}")
                        return False
                else:
                    self.log_test("Get Orders Count After Import", False, "Failed to get order count after import")
                    return False
            else:
                error_msg = f"Import failed with status {response.status_code}: {response.text}"
                self.log_test("Excel File Import", False, error_msg)
                return False
                
        except Exception as e:
            self.log_test("Excel File Import", False, f"Import request failed: {str(e)}")
            return False
        
        return False

    def test_service_rates_initialization(self):
        """Test if service rates were properly initialized in the database"""
        print("\n💰 Testing Service Rates Initialization...")
        
        success, response = self.run_test("Get Service Rates", "GET", "rates", 200)
        
        if success and response:
            rates = response if isinstance(response, list) else []
            
            # Check if we have the expected number of rates (18 based on SK_Rates data)
            expected_count = 18
            if len(rates) >= expected_count:
                self.log_test("Service Rates Count", True, f"Found {len(rates)} service rates (expected >= {expected_count})")
                
                # Check for specific rate combinations
                expected_combinations = [
                    ("Kawale Cranes", "Europ Assistance", "2 Wheeler Towing"),
                    ("Kawale Cranes", "Europ Assistance", "Under-lift"),
                    ("Kawale Cranes", "Europ Assistance", "FBT"),
                    ("Vidharbha Towing", "TVS", "Under-lift"),
                    ("Kawale Cranes", "Mondial", "2 Wheeler Towing")
                ]
                
                found_combinations = 0
                for rate in rates:
                    for firm, company, service in expected_combinations:
                        if (rate.get('name_of_firm') == firm and 
                            rate.get('company_name') == company and 
                            rate.get('service_type') == service):
                            found_combinations += 1
                            break
                
                if found_combinations >= 3:
                    self.log_test("Service Rates Content", True, f"Found {found_combinations} expected rate combinations")
                    return True
                else:
                    self.log_test("Service Rates Content", False, f"Only found {found_combinations} expected combinations")
            else:
                self.log_test("Service Rates Count", False, f"Found {len(rates)} rates, expected >= {expected_count}")
        
        return False

    def test_get_service_rates_endpoint(self):
        """Test /api/rates endpoint (Admin/Super Admin only)"""
        print("\n📊 Testing Service Rates Endpoint...")
        
        # Test with admin token
        success1, response1 = self.run_test("Get Service Rates (Admin)", "GET", "rates", 200)
        
        if success1 and response1:
            rates = response1 if isinstance(response1, list) else []
            
            # Verify rate structure
            if rates and len(rates) > 0:
                sample_rate = rates[0]
                required_fields = ['name_of_firm', 'company_name', 'service_type', 'base_rate', 'rate_per_km_beyond']
                
                has_all_fields = all(field in sample_rate for field in required_fields)
                if has_all_fields:
                    self.log_test("Service Rate Structure", True, f"Rate has all required fields: {required_fields}")
                    
                    # Check specific rate values
                    kawale_europ_2wheeler = next((r for r in rates if 
                                                r.get('name_of_firm') == 'Kawale Cranes' and 
                                                r.get('company_name') == 'Europ Assistance' and 
                                                r.get('service_type') == '2 Wheeler Towing'), None)
                    
                    if kawale_europ_2wheeler:
                        expected_base_rate = 1200
                        expected_per_km = 12
                        actual_base = kawale_europ_2wheeler.get('base_rate')
                        actual_per_km = kawale_europ_2wheeler.get('rate_per_km_beyond')
                        
                        if actual_base == expected_base_rate and actual_per_km == expected_per_km:
                            self.log_test("Specific Rate Values", True, f"Kawale-Europ-2Wheeler: Base={actual_base}, PerKm={actual_per_km}")
                            return True
                        else:
                            self.log_test("Specific Rate Values", False, f"Expected Base={expected_base_rate}, PerKm={expected_per_km}, Got Base={actual_base}, PerKm={actual_per_km}")
                    else:
                        self.log_test("Specific Rate Values", False, "Could not find Kawale Cranes - Europ Assistance - 2 Wheeler Towing rate")
                else:
                    self.log_test("Service Rate Structure", False, f"Missing fields in rate: {sample_rate}")
            else:
                self.log_test("Service Rate Structure", False, "No rates returned")
        
        return False

    def test_create_company_orders_for_financials(self):
        """Create company orders with different scenarios for financial testing"""
        print("\n🏢 Creating Company Orders for Financial Testing...")
        
        # Test order 1: Base distance (≤40km) - Kawale Cranes, Europ Assistance, 2 Wheeler Towing
        order1_data = {
            "customer_name": "Financial Test Base Distance",
            "phone": "9876543280",
            "order_type": "company",
            "name_of_firm": "Kawale Cranes",
            "company_name": "Europ Assistance", 
            "company_service_type": "2 Wheeler Towing",
            "case_id_file_number": "FIN001",
            "company_trip_from": "Mumbai Central",
            "company_trip_to": "Bandra",
            "company_kms_travelled": 25.0,  # Within base distance
            "company_vehicle_name": "Honda Activa",
            "company_vehicle_number": "MH01AB1234"
        }
        
        success1, response1 = self.run_test("Create Company Order (Base Distance)", "POST", "orders", 200, order1_data)
        if success1 and 'id' in response1:
            self.created_orders.append(response1['id'])
            self.base_distance_order_id = response1['id']
        
        # Test order 2: Beyond base distance (>40km) - Vidharbha Towing, TVS, Under-lift
        order2_data = {
            "customer_name": "Financial Test Beyond Distance",
            "phone": "9876543281",
            "order_type": "company",
            "name_of_firm": "Vidharbha Towing",
            "company_name": "TVS",
            "company_service_type": "Under-lift",
            "case_id_file_number": "FIN002",
            "company_trip_from": "Nagpur",
            "company_trip_to": "Wardha",
            "company_kms_travelled": 65.0,  # Beyond base distance (40km)
            "company_vehicle_name": "TVS Apache",
            "company_vehicle_number": "MH31CD5678"
        }
        
        success2, response2 = self.run_test("Create Company Order (Beyond Distance)", "POST", "orders", 200, order2_data)
        if success2 and 'id' in response2:
            self.created_orders.append(response2['id'])
            self.beyond_distance_order_id = response2['id']
        
        # Test order 3: With incentive - Kawale Cranes, Mondial, Under-lift
        order3_data = {
            "customer_name": "Financial Test With Incentive",
            "phone": "9876543282",
            "order_type": "company",
            "name_of_firm": "Kawale Cranes",
            "company_name": "Mondial",
            "company_service_type": "Under-lift",
            "case_id_file_number": "FIN003",
            "company_trip_from": "Pune",
            "company_trip_to": "Nashik",
            "company_kms_travelled": 55.0,  # Beyond base distance
            "company_vehicle_name": "Maruti Swift",
            "company_vehicle_number": "MH12EF9012",
            "incentive_amount": 500.0,
            "incentive_reason": "Excellent service and quick response"
        }
        
        success3, response3 = self.run_test("Create Company Order (With Incentive)", "POST", "orders", 200, order3_data)
        if success3 and 'id' in response3:
            self.created_orders.append(response3['id'])
            self.incentive_order_id = response3['id']
        
        return success1 and success2 and success3

    def test_financial_calculations_base_distance(self):
        """Test financial calculations for base distance (≤40km)"""
        print("\n💰 Testing Financial Calculations - Base Distance...")
        
        if not hasattr(self, 'base_distance_order_id'):
            return self.log_test("Financial Calc Base Distance", False, "No base distance order created")
        
        success, response = self.run_test("Get Financials (Base Distance)", "GET", f"orders/{self.base_distance_order_id}/financials", 200)
        
        if success and response:
            base_revenue = response.get('base_revenue', 0)
            incentive_amount = response.get('incentive_amount', 0)
            total_revenue = response.get('total_revenue', 0)
            calculation_details = response.get('calculation_details', '')
            
            # Expected: Kawale Cranes - Europ Assistance - 2 Wheeler Towing = Base rate 1200 for ≤40km
            expected_base_revenue = 1200.0
            expected_total = expected_base_revenue + incentive_amount
            
            if base_revenue == expected_base_revenue and total_revenue == expected_total:
                self.log_test("Base Distance Calculation", True, f"Base: ₹{base_revenue}, Total: ₹{total_revenue}, Details: {calculation_details}")
                return True
            else:
                self.log_test("Base Distance Calculation", False, f"Expected Base: ₹{expected_base_revenue}, Got: ₹{base_revenue}, Total: ₹{total_revenue}")
        
        return False

    def test_financial_calculations_beyond_distance(self):
        """Test financial calculations for beyond base distance (>40km)"""
        print("\n💰 Testing Financial Calculations - Beyond Distance...")
        
        if not hasattr(self, 'beyond_distance_order_id'):
            return self.log_test("Financial Calc Beyond Distance", False, "No beyond distance order created")
        
        success, response = self.run_test("Get Financials (Beyond Distance)", "GET", f"orders/{self.beyond_distance_order_id}/financials", 200)
        
        if success and response:
            base_revenue = response.get('base_revenue', 0)
            incentive_amount = response.get('incentive_amount', 0)
            total_revenue = response.get('total_revenue', 0)
            calculation_details = response.get('calculation_details', '')
            
            # Expected: Vidharbha Towing - TVS - Under-lift = Base 1700 + (65-40) * 17 = 1700 + 425 = 2125
            expected_base_rate = 1700.0
            expected_per_km = 17.0
            kms_travelled = 65.0
            excess_km = kms_travelled - 40.0  # 25km excess
            expected_base_revenue = expected_base_rate + (excess_km * expected_per_km)  # 1700 + (25 * 17) = 2125
            expected_total = expected_base_revenue + incentive_amount
            
            if base_revenue == expected_base_revenue and total_revenue == expected_total:
                self.log_test("Beyond Distance Calculation", True, f"Base: ₹{base_revenue}, Total: ₹{total_revenue}, Details: {calculation_details}")
                return True
            else:
                self.log_test("Beyond Distance Calculation", False, f"Expected Base: ₹{expected_base_revenue}, Got: ₹{base_revenue}, Total: ₹{total_revenue}")
        
        return False

    def test_financial_calculations_with_incentive(self):
        """Test financial calculations including incentive amount"""
        print("\n💰 Testing Financial Calculations - With Incentive...")
        
        if not hasattr(self, 'incentive_order_id'):
            return self.log_test("Financial Calc With Incentive", False, "No incentive order created")
        
        success, response = self.run_test("Get Financials (With Incentive)", "GET", f"orders/{self.incentive_order_id}/financials", 200)
        
        if success and response:
            base_revenue = response.get('base_revenue', 0)
            incentive_amount = response.get('incentive_amount', 0)
            total_revenue = response.get('total_revenue', 0)
            calculation_details = response.get('calculation_details', '')
            
            # Expected: Kawale Cranes - Mondial - Under-lift = Base 1400 + (55-40) * 15 = 1400 + 225 = 1625
            # Plus incentive: 1625 + 500 = 2125
            expected_base_rate = 1400.0
            expected_per_km = 15.0
            kms_travelled = 55.0
            excess_km = kms_travelled - 40.0  # 15km excess
            expected_base_revenue = expected_base_rate + (excess_km * expected_per_km)  # 1400 + (15 * 15) = 1625
            expected_incentive = 500.0
            expected_total = expected_base_revenue + expected_incentive  # 1625 + 500 = 2125
            
            if (base_revenue == expected_base_revenue and 
                incentive_amount == expected_incentive and 
                total_revenue == expected_total):
                self.log_test("Incentive Calculation", True, f"Base: ₹{base_revenue}, Incentive: ₹{incentive_amount}, Total: ₹{total_revenue}")
                return True
            else:
                self.log_test("Incentive Calculation", False, f"Expected Base: ₹{expected_base_revenue}, Incentive: ₹{expected_incentive}, Total: ₹{expected_total}, Got Base: ₹{base_revenue}, Incentive: ₹{incentive_amount}, Total: ₹{total_revenue}")
        
        return False

    def test_financial_calculations_no_rate_found(self):
        """Test financial calculations when no rate is found"""
        print("\n💰 Testing Financial Calculations - No Rate Found...")
        
        # Create order with combination that doesn't exist in rates
        order_data = {
            "customer_name": "No Rate Test",
            "phone": "9876543283",
            "order_type": "company",
            "name_of_firm": "Unknown Firm",
            "company_name": "Unknown Company",
            "company_service_type": "Unknown Service",
            "case_id_file_number": "NORATE001",
            "company_trip_from": "Test From",
            "company_trip_to": "Test To",
            "company_kms_travelled": 30.0
        }
        
        success1, response1 = self.run_test("Create Order (No Rate)", "POST", "orders", 200, order_data)
        if success1 and 'id' in response1:
            self.created_orders.append(response1['id'])
            order_id = response1['id']
            
            # Test financial calculation
            success2, response2 = self.run_test("Get Financials (No Rate)", "GET", f"orders/{order_id}/financials", 200)
            
            if success2 and response2:
                base_revenue = response2.get('base_revenue', 0)
                total_revenue = response2.get('total_revenue', 0)
                calculation_details = response2.get('calculation_details', '')
                
                # Should return 0 base revenue with appropriate message
                if base_revenue == 0 and "No rate found" in calculation_details:
                    self.log_test("No Rate Found Handling", True, f"Correctly handled no rate: {calculation_details}")
                    return True
                else:
                    self.log_test("No Rate Found Handling", False, f"Base: ₹{base_revenue}, Details: {calculation_details}")
        
        return False

    def test_financial_calculations_cash_order(self):
        """Test that financial calculations return empty for cash orders"""
        print("\n💰 Testing Financial Calculations - Cash Order...")
        
        # Create a cash order
        cash_order_data = {
            "customer_name": "Cash Order Financial Test",
            "phone": "9876543284",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune",
            "cash_vehicle_name": "Tata ACE",
            "amount_received": 5000.0
        }
        
        success1, response1 = self.run_test("Create Cash Order for Financial Test", "POST", "orders", 200, cash_order_data)
        if success1 and 'id' in response1:
            self.created_orders.append(response1['id'])
            order_id = response1['id']
            
            # Test financial calculation on cash order
            success2, response2 = self.run_test("Get Financials (Cash Order)", "GET", f"orders/{order_id}/financials", 200)
            
            if success2 and response2:
                base_revenue = response2.get('base_revenue', 0)
                total_revenue = response2.get('total_revenue', 0)
                
                # Should return 0 for cash orders
                if base_revenue == 0 and total_revenue == 0:
                    self.log_test("Cash Order Financial Calc", True, "Correctly returns 0 for cash orders")
                    return True
                else:
                    self.log_test("Cash Order Financial Calc", False, f"Expected 0, got Base: ₹{base_revenue}, Total: ₹{total_revenue}")
        
        return False

    def test_sk_rates_calculation_system(self):
        """Comprehensive test of SK Rates calculation system"""
        print("\n🧮 Testing SK Rates Calculation System...")
        
        # Test service rates initialization
        rates_init = self.test_service_rates_initialization()
        
        # Test get service rates endpoint
        rates_endpoint = self.test_get_service_rates_endpoint()
        
        # Create test orders for financial calculations
        orders_created = self.test_create_company_orders_for_financials()
        
        # Test financial calculations
        base_calc = self.test_financial_calculations_base_distance()
        beyond_calc = self.test_financial_calculations_beyond_distance()
        incentive_calc = self.test_financial_calculations_with_incentive()
        no_rate_calc = self.test_financial_calculations_no_rate_found()
        cash_calc = self.test_financial_calculations_cash_order()
        
        # Overall success
        all_passed = all([rates_init, rates_endpoint, orders_created, base_calc, beyond_calc, incentive_calc, no_rate_calc, cash_calc])
        
        if all_passed:
            self.log_test("SK Rates System Overall", True, "All SK Rates calculation tests passed")
        else:
            failed_tests = []
            if not rates_init: failed_tests.append("Rates Initialization")
            if not rates_endpoint: failed_tests.append("Rates Endpoint")
            if not orders_created: failed_tests.append("Test Orders Creation")
            if not base_calc: failed_tests.append("Base Distance Calc")
            if not beyond_calc: failed_tests.append("Beyond Distance Calc")
            if not incentive_calc: failed_tests.append("Incentive Calc")
            if not no_rate_calc: failed_tests.append("No Rate Handling")
            if not cash_calc: failed_tests.append("Cash Order Calc")
            
            self.log_test("SK Rates System Overall", False, f"Failed tests: {', '.join(failed_tests)}")
        
        return all_passed

    def test_mandatory_fields_validation_comprehensive(self):
        """Comprehensive test of mandatory fields validation for company orders"""
        print("\n🔒 Testing Mandatory Fields Validation - COMPREHENSIVE...")
        
        # Test 1: Company order missing Company Name (should fail with HTTP 422)
        missing_company_name = {
            "customer_name": "Test Missing Company Name",
            "phone": "9876543290",
            "order_type": "company",
            "company_service_type": "2 Wheeler Towing",
            "company_driver_details": "Rahul",
            "company_towing_vehicle": "Tata ACE"
            # Missing company_name
        }
        
        success1, response1 = self.run_test("Company Order Missing Company Name", "POST", "orders", 422, missing_company_name)
        if success1 and response1:
            detail = response1.get('detail', '')
            if 'Company Name' in detail:
                self.log_test("Company Name Error Message", True, f"Correct error: {detail}")
            else:
                self.log_test("Company Name Error Message", False, f"Unexpected error: {detail}")
        
        # Test 2: Company order with empty Company Name (should fail with HTTP 422)
        empty_company_name = {
            "customer_name": "Test Empty Company Name",
            "phone": "9876543291",
            "order_type": "company",
            "company_name": "",  # Empty string
            "company_service_type": "Under-lift",
            "company_driver_details": "Subhash",
            "company_towing_vehicle": "Mahindra Bolero"
        }
        
        success2, response2 = self.run_test("Company Order Empty Company Name", "POST", "orders", 422, empty_company_name)
        
        # Test 3: Company order missing Service Type (should fail with HTTP 422)
        missing_service_type = {
            "customer_name": "Test Missing Service Type",
            "phone": "9876543292",
            "order_type": "company",
            "company_name": "Europ Assistance",
            "company_driver_details": "Dubey",
            "company_towing_vehicle": "Tata ACE"
            # Missing company_service_type
        }
        
        success3, response3 = self.run_test("Company Order Missing Service Type", "POST", "orders", 422, missing_service_type)
        if success3 and response3:
            detail = response3.get('detail', '')
            if 'Service Type' in detail:
                self.log_test("Service Type Error Message", True, f"Correct error: {detail}")
            else:
                self.log_test("Service Type Error Message", False, f"Unexpected error: {detail}")
        
        # Test 4: Company order with empty Service Type (should fail with HTTP 422)
        empty_service_type = {
            "customer_name": "Test Empty Service Type",
            "phone": "9876543293",
            "order_type": "company",
            "company_name": "Mondial",
            "company_service_type": "",  # Empty string
            "company_driver_details": "Sudhir",
            "company_towing_vehicle": "Mahindra Bolero"
        }
        
        success4, response4 = self.run_test("Company Order Empty Service Type", "POST", "orders", 422, empty_service_type)
        
        # Test 5: Company order missing Driver (should fail with HTTP 422)
        missing_driver = {
            "customer_name": "Test Missing Driver",
            "phone": "9876543294",
            "order_type": "company",
            "company_name": "TVS",
            "company_service_type": "FBT",
            "company_towing_vehicle": "Tata ACE"
            # Missing company_driver_details
        }
        
        success5, response5 = self.run_test("Company Order Missing Driver", "POST", "orders", 422, missing_driver)
        if success5 and response5:
            detail = response5.get('detail', '')
            if 'Driver' in detail:
                self.log_test("Driver Error Message", True, f"Correct error: {detail}")
            else:
                self.log_test("Driver Error Message", False, f"Unexpected error: {detail}")
        
        # Test 6: Company order with empty Driver (should fail with HTTP 422)
        empty_driver = {
            "customer_name": "Test Empty Driver",
            "phone": "9876543295",
            "order_type": "company",
            "company_name": "Europ Assistance",
            "company_service_type": "2 Wheeler Towing",
            "company_driver_details": "",  # Empty string
            "company_towing_vehicle": "Tata ACE"
        }
        
        success6, response6 = self.run_test("Company Order Empty Driver", "POST", "orders", 422, empty_driver)
        
        # Test 7: Company order missing Towing Vehicle (should fail with HTTP 422)
        missing_towing_vehicle = {
            "customer_name": "Test Missing Towing Vehicle",
            "phone": "9876543296",
            "order_type": "company",
            "company_name": "Mondial",
            "company_service_type": "Under-lift",
            "company_driver_details": "Vikas"
            # Missing company_towing_vehicle
        }
        
        success7, response7 = self.run_test("Company Order Missing Towing Vehicle", "POST", "orders", 422, missing_towing_vehicle)
        if success7 and response7:
            detail = response7.get('detail', '')
            if 'Towing Vehicle' in detail:
                self.log_test("Towing Vehicle Error Message", True, f"Correct error: {detail}")
            else:
                self.log_test("Towing Vehicle Error Message", False, f"Unexpected error: {detail}")
        
        # Test 8: Company order with empty Towing Vehicle (should fail with HTTP 422)
        empty_towing_vehicle = {
            "customer_name": "Test Empty Towing Vehicle",
            "phone": "9876543297",
            "order_type": "company",
            "company_name": "TVS",
            "company_service_type": "FBT",
            "company_driver_details": "Rahul",
            "company_towing_vehicle": ""  # Empty string
        }
        
        success8, response8 = self.run_test("Company Order Empty Towing Vehicle", "POST", "orders", 422, empty_towing_vehicle)
        
        # Test 9: Company order missing multiple fields (should fail with HTTP 422 listing all)
        missing_multiple_fields = {
            "customer_name": "Test Missing Multiple Fields",
            "phone": "9876543298",
            "order_type": "company"
            # Missing company_name, company_service_type, company_driver_details, company_towing_vehicle
        }
        
        success9, response9 = self.run_test("Company Order Missing Multiple Fields", "POST", "orders", 422, missing_multiple_fields)
        if success9 and response9:
            detail = response9.get('detail', '')
            required_fields = ['Company Name', 'Service Type', 'Driver', 'Towing Vehicle']
            found_fields = sum(1 for field in required_fields if field in detail)
            if found_fields >= 3:  # Should mention most/all missing fields
                self.log_test("Multiple Fields Error Message", True, f"Lists multiple missing fields: {detail}")
            else:
                self.log_test("Multiple Fields Error Message", False, f"Should list multiple fields: {detail}")
        
        # Test 10: Valid company order with all mandatory fields (should succeed with HTTP 200/201)
        valid_company_order = {
            "customer_name": "Test Valid Company Order",
            "phone": "9876543299",
            "order_type": "company",
            "company_name": "Europ Assistance",
            "company_service_type": "2 Wheeler Towing",
            "company_driver_details": "Rahul",
            "company_towing_vehicle": "Tata ACE",
            "name_of_firm": "Kawale Cranes",
            "case_id_file_number": "VALID001",
            "company_trip_from": "Mumbai",
            "company_trip_to": "Pune"
        }
        
        success10, response10 = self.run_test("Valid Company Order with All Mandatory Fields", "POST", "orders", 200, valid_company_order)
        if success10 and 'id' in response10:
            self.created_orders.append(response10['id'])
            # Verify all mandatory fields are stored correctly
            checks = [
                ('company_name', 'Europ Assistance'),
                ('company_service_type', '2 Wheeler Towing'),
                ('company_driver_details', 'Rahul'),
                ('company_towing_vehicle', 'Tata ACE')
            ]
            
            all_correct = True
            for field, expected in checks:
                actual = response10.get(field)
                if actual != expected:
                    self.log_test(f"Valid Order {field} Storage", False, f"Expected: {expected}, Got: {actual}")
                    all_correct = False
            
            if all_correct:
                self.log_test("Valid Order Mandatory Fields Storage", True, "All mandatory fields stored correctly")
        
        # Count successful validation tests (should fail appropriately)
        validation_tests = [success1, success2, success3, success4, success5, success6, success7, success8, success9]
        validation_success_count = sum(validation_tests)
        
        # Valid order should succeed
        overall_success = validation_success_count == 9 and success10
        
        if overall_success:
            self.log_test("Mandatory Fields Validation Overall", True, f"All validation tests passed: {validation_success_count}/9 validation failures + 1 valid success")
        else:
            self.log_test("Mandatory Fields Validation Overall", False, f"Validation tests: {validation_success_count}/9, Valid order: {success10}")
        
        return overall_success

    def test_mandatory_fields_update_validation(self):
        """Test mandatory fields validation on order updates"""
        print("\n🔄 Testing Mandatory Fields Validation - UPDATE Operations...")
        
        # First create a valid company order
        valid_company_order = {
            "customer_name": "Update Test Order",
            "phone": "9876543302",
            "order_type": "company",
            "company_name": "Europ Assistance",
            "company_service_type": "2 Wheeler Towing",
            "company_driver_details": "Rahul",
            "company_towing_vehicle": "Tata ACE",
            "name_of_firm": "Kawale Cranes",
            "case_id_file_number": "UPDATE001"
        }
        
        success_create, response_create = self.run_test("Create Order for Update Test", "POST", "orders", 200, valid_company_order)
        if not success_create or 'id' not in response_create:
            return self.log_test("Update Validation Test", False, "Failed to create test order")
        
        order_id = response_create['id']
        self.created_orders.append(order_id)
        
        # Test 1: Update to remove Company Name (should fail)
        update_remove_company_name = {
            "company_name": ""  # Empty string
        }
        
        success1, _ = self.run_test("Update Remove Company Name", "PUT", f"orders/{order_id}", 422, update_remove_company_name)
        
        # Test 2: Update to remove Service Type (should fail)
        update_remove_service_type = {
            "company_service_type": ""  # Empty string
        }
        
        success2, _ = self.run_test("Update Remove Service Type", "PUT", f"orders/{order_id}", 422, update_remove_service_type)
        
        # Test 3: Update to remove Driver (should fail)
        update_remove_driver = {
            "company_driver_details": ""  # Empty string
        }
        
        success3, _ = self.run_test("Update Remove Driver", "PUT", f"orders/{order_id}", 422, update_remove_driver)
        
        # Test 4: Update to remove Towing Vehicle (should fail)
        update_remove_towing_vehicle = {
            "company_towing_vehicle": ""  # Empty string
        }
        
        success4, _ = self.run_test("Update Remove Towing Vehicle", "PUT", f"orders/{order_id}", 422, update_remove_towing_vehicle)
        
        # Test 5: Valid update (should succeed)
        valid_update = {
            "company_name": "Mondial",
            "company_service_type": "Under-lift",
            "company_driver_details": "Subhash",
            "company_towing_vehicle": "Mahindra Bolero"
        }
        
        success5, response5 = self.run_test("Valid Update with All Mandatory Fields", "PUT", f"orders/{order_id}", 200, valid_update)
        
        # Verify the update worked
        if success5 and response5:
            checks = [
                ('company_name', 'Mondial'),
                ('company_service_type', 'Under-lift'),
                ('company_driver_details', 'Subhash'),
                ('company_towing_vehicle', 'Mahindra Bolero')
            ]
            
            all_correct = True
            for field, expected in checks:
                actual = response5.get(field)
                if actual != expected:
                    self.log_test(f"Update {field} Verification", False, f"Expected: {expected}, Got: {actual}")
                    all_correct = False
            
            if all_correct:
                self.log_test("Valid Update Verification", True, "All mandatory fields updated correctly")
        
        validation_tests = [success1, success2, success3, success4]
        validation_success_count = sum(validation_tests)
        overall_success = validation_success_count == 4 and success5
        
        if overall_success:
            self.log_test("Update Validation Overall", True, f"All update validation tests passed: {validation_success_count}/4 validation failures + 1 valid success")
        else:
            self.log_test("Update Validation Overall", False, f"Update validation tests: {validation_success_count}/4, Valid update: {success5}")
        
        return overall_success

    def test_cash_orders_no_validation(self):
        """Test that cash orders don't require company mandatory fields"""
        print("\n💰 Testing Cash Orders - No Company Field Validation...")
        
        # Test 1: Cash order without any company fields (should succeed)
        cash_order_no_company_fields = {
            "customer_name": "Cash Order No Company Fields",
            "phone": "9876543300",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune",
            "cash_vehicle_name": "Tata ACE",
            "amount_received": 5000.0
        }
        
        success1, response1 = self.run_test("Cash Order No Company Fields", "POST", "orders", 200, cash_order_no_company_fields)
        if success1 and 'id' in response1:
            self.created_orders.append(response1['id'])
        
        # Test 2: Cash order with empty company fields (should succeed)
        cash_order_empty_company_fields = {
            "customer_name": "Cash Order Empty Company Fields",
            "phone": "9876543301",
            "order_type": "cash",
            "company_name": "",  # Empty - should be allowed for cash orders
            "company_service_type": "",  # Empty - should be allowed for cash orders
            "company_driver_details": "",  # Empty - should be allowed for cash orders
            "company_towing_vehicle": "",  # Empty - should be allowed for cash orders
            "cash_trip_from": "Delhi",
            "cash_trip_to": "Gurgaon",
            "cash_vehicle_name": "Mahindra Bolero",
            "amount_received": 3000.0
        }
        
        success2, response2 = self.run_test("Cash Order Empty Company Fields", "POST", "orders", 200, cash_order_empty_company_fields)
        if success2 and 'id' in response2:
            self.created_orders.append(response2['id'])
        
        overall_success = success1 and success2
        
        if overall_success:
            self.log_test("Cash Orders No Validation", True, "Cash orders correctly bypass company field validation")
        else:
            self.log_test("Cash Orders No Validation", False, f"Cash order tests failed: {success1}, {success2}")
        
        return overall_success

    def test_incentive_functionality_regression(self):
        """Test that incentive functionality still works for both order types"""
        print("\n🎁 Testing Incentive Functionality - Regression Test...")
        
        # Test 1: Cash order with incentive (should succeed)
        cash_order_with_incentive = {
            "customer_name": "Cash Incentive Test",
            "phone": "9876543303",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune",
            "cash_vehicle_name": "Tata ACE",
            "amount_received": 5000.0,
            "incentive_amount": 500.0,
            "incentive_reason": "Excellent service"
        }
        
        success1, response1 = self.run_test("Cash Order with Incentive", "POST", "orders", 200, cash_order_with_incentive)
        if success1 and 'id' in response1:
            self.created_orders.append(response1['id'])
            # Verify incentive fields
            if (response1.get('incentive_amount') == 500.0 and 
                response1.get('incentive_reason') == "Excellent service"):
                self.log_test("Cash Order Incentive Storage", True, "Incentive fields stored correctly")
            else:
                self.log_test("Cash Order Incentive Storage", False, f"Incentive: {response1.get('incentive_amount')}, Reason: {response1.get('incentive_reason')}")
        
        # Test 2: Company order with incentive (should succeed)
        company_order_with_incentive = {
            "customer_name": "Company Incentive Test",
            "phone": "9876543304",
            "order_type": "company",
            "company_name": "Europ Assistance",
            "company_service_type": "2 Wheeler Towing",
            "company_driver_details": "Rahul",
            "company_towing_vehicle": "Tata ACE",
            "name_of_firm": "Kawale Cranes",
            "case_id_file_number": "INC001",
            "incentive_amount": 750.0,
            "incentive_reason": "Quick response time"
        }
        
        success2, response2 = self.run_test("Company Order with Incentive", "POST", "orders", 200, company_order_with_incentive)
        if success2 and 'id' in response2:
            self.created_orders.append(response2['id'])
            # Verify incentive fields
            if (response2.get('incentive_amount') == 750.0 and 
                response2.get('incentive_reason') == "Quick response time"):
                self.log_test("Company Order Incentive Storage", True, "Incentive fields stored correctly")
            else:
                self.log_test("Company Order Incentive Storage", False, f"Incentive: {response2.get('incentive_amount')}, Reason: {response2.get('incentive_reason')}")
        
        overall_success = success1 and success2
        
        if overall_success:
            self.log_test("Incentive Functionality Regression", True, "Incentive functionality working for both order types")
        else:
            self.log_test("Incentive Functionality Regression", False, f"Incentive tests failed: Cash={success1}, Company={success2}")
        
        return overall_success

    def test_revenue_calculations_regression(self):
        """Test that revenue calculations still work after validation changes"""
        print("\n💰 Testing Revenue Calculations - Regression Test...")
        
        # Create a company order with all mandatory fields and known rate
        company_order_for_revenue = {
            "customer_name": "Revenue Calculation Test",
            "phone": "9876543305",
            "order_type": "company",
            "name_of_firm": "Kawale Cranes",
            "company_name": "Europ Assistance",
            "company_service_type": "2 Wheeler Towing",
            "company_driver_details": "Rahul",
            "company_towing_vehicle": "Tata ACE",
            "case_id_file_number": "REV001",
            "company_kms_travelled": 30.0,  # Within base distance
            "incentive_amount": 200.0,
            "incentive_reason": "Good service"
        }
        
        success1, response1 = self.run_test("Create Order for Revenue Test", "POST", "orders", 200, company_order_for_revenue)
        if success1 and 'id' in response1:
            self.created_orders.append(response1['id'])
            order_id = response1['id']
            
            # Test financial calculation
            success2, response2 = self.run_test("Get Revenue Calculation", "GET", f"orders/{order_id}/financials", 200)
            
            if success2 and response2:
                base_revenue = response2.get('base_revenue', 0)
                incentive_amount = response2.get('incentive_amount', 0)
                total_revenue = response2.get('total_revenue', 0)
                
                # Expected: Kawale Cranes - Europ Assistance - 2 Wheeler Towing = 1200 base + 200 incentive = 1400
                expected_base = 1200.0
                expected_incentive = 200.0
                expected_total = 1400.0
                
                if (base_revenue == expected_base and 
                    incentive_amount == expected_incentive and 
                    total_revenue == expected_total):
                    self.log_test("Revenue Calculation Regression", True, f"Base: ₹{base_revenue}, Incentive: ₹{incentive_amount}, Total: ₹{total_revenue}")
                    return True
                else:
                    self.log_test("Revenue Calculation Regression", False, f"Expected Base: ₹{expected_base}, Incentive: ₹{expected_incentive}, Total: ₹{expected_total}, Got Base: ₹{base_revenue}, Incentive: ₹{incentive_amount}, Total: ₹{total_revenue}")
        
        return False

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

    def test_mandatory_fields_validation(self):
        """Test mandatory fields validation for company orders"""
        print("\n🔒 Testing Mandatory Fields Validation...")
        
        # Test 1: Company order missing Company Name (should fail)
        missing_company_name = {
            "customer_name": "Test Missing Company Name",
            "phone": "9876543290",
            "order_type": "company",
            "company_service_type": "2 Wheeler Towing",
            "company_driver_details": "Rahul",
            "company_towing_vehicle": "Tata ACE"
            # Missing company_name
        }
        
        success1, _ = self.run_test("Company Order Missing Company Name", "POST", "orders", 422, missing_company_name)
        
        # Test 2: Company order missing Service Type (should fail)
        missing_service_type = {
            "customer_name": "Test Missing Service Type",
            "phone": "9876543291",
            "order_type": "company",
            "company_name": "Europ Assistance",
            "company_driver_details": "Subhash",
            "company_towing_vehicle": "Mahindra Bolero"
            # Missing company_service_type
        }
        
        success2, _ = self.run_test("Company Order Missing Service Type", "POST", "orders", 422, missing_service_type)
        
        # Test 3: Company order missing Driver (should fail)
        missing_driver = {
            "customer_name": "Test Missing Driver",
            "phone": "9876543292",
            "order_type": "company",
            "company_name": "Mondial",
            "company_service_type": "Under-lift",
            "company_towing_vehicle": "Tata ACE"
            # Missing company_driver_details
        }
        
        success3, _ = self.run_test("Company Order Missing Driver", "POST", "orders", 422, missing_driver)
        
        # Test 4: Company order missing Towing Vehicle (should fail)
        missing_towing_vehicle = {
            "customer_name": "Test Missing Towing Vehicle",
            "phone": "9876543293",
            "order_type": "company",
            "company_name": "TVS",
            "company_service_type": "FBT",
            "company_driver_details": "Vikas"
            # Missing company_towing_vehicle
        }
        
        success4, _ = self.run_test("Company Order Missing Towing Vehicle", "POST", "orders", 422, missing_towing_vehicle)
        
        # Test 5: Valid company order with all mandatory fields (should succeed)
        valid_company_order = {
            "customer_name": "Test Valid Company Order",
            "phone": "9876543294",
            "order_type": "company",
            "company_name": "Europ Assistance",
            "company_service_type": "2 Wheeler Towing",
            "company_driver_details": "Rahul",
            "company_towing_vehicle": "Tata ACE",
            "name_of_firm": "Kawale Cranes",
            "case_id_file_number": "VALID001",
            "company_trip_from": "Mumbai",
            "company_trip_to": "Pune"
        }
        
        success5, response5 = self.run_test("Valid Company Order with All Mandatory Fields", "POST", "orders", 200, valid_company_order)
        if success5 and 'id' in response5:
            self.created_orders.append(response5['id'])
        
        # Test 6: Cash order should not require company mandatory fields (should succeed)
        cash_order_no_company_fields = {
            "customer_name": "Test Cash Order",
            "phone": "9876543295",
            "order_type": "cash",
            "cash_trip_from": "Delhi",
            "cash_trip_to": "Gurgaon",
            "amount_received": 3000.0
            # No company fields required for cash orders
        }
        
        success6, response6 = self.run_test("Cash Order Without Company Fields", "POST", "orders", 200, cash_order_no_company_fields)
        if success6 and 'id' in response6:
            self.created_orders.append(response6['id'])
        
        all_passed = success1 and success2 and success3 and success4 and success5 and success6
        
        if all_passed:
            self.log_test("Mandatory Fields Validation Overall", True, "All mandatory field validation tests passed")
        else:
            failed_tests = []
            if not success1: failed_tests.append("Missing Company Name")
            if not success2: failed_tests.append("Missing Service Type")
            if not success3: failed_tests.append("Missing Driver")
            if not success4: failed_tests.append("Missing Towing Vehicle")
            if not success5: failed_tests.append("Valid Company Order")
            if not success6: failed_tests.append("Cash Order")
            
            self.log_test("Mandatory Fields Validation Overall", False, f"Failed tests: {', '.join(failed_tests)}")
        
        return all_passed

    def test_incentive_functionality_company_orders(self):
        """Test incentive functionality specifically for company orders"""
        print("\n💰 Testing Incentive Functionality for Company Orders...")
        
        # Test 1: Create company order with incentive amount and reason
        company_order_with_incentive = {
            "customer_name": "Test Company Incentive",
            "phone": "9876543296",
            "order_type": "company",
            "company_name": "Europ Assistance",
            "company_service_type": "Under-lift",
            "company_driver_details": "Subhash",
            "company_towing_vehicle": "Mahindra Bolero",
            "name_of_firm": "Kawale Cranes",
            "case_id_file_number": "INC001",
            "company_trip_from": "Mumbai",
            "company_trip_to": "Pune",
            "company_kms_travelled": 45.0,  # Beyond base distance for calculation
            "incentive_amount": 750.0,
            "incentive_reason": "Exceptional service and quick response time"
        }
        
        success1, response1 = self.run_test("Company Order with Incentive", "POST", "orders", 200, company_order_with_incentive)
        incentive_order_id = None
        if success1 and 'id' in response1:
            self.created_orders.append(response1['id'])
            incentive_order_id = response1['id']
            
            # Verify incentive fields are stored correctly
            incentive_amount_correct = response1.get('incentive_amount') == 750.0
            incentive_reason_correct = response1.get('incentive_reason') == "Exceptional service and quick response time"
            
            if incentive_amount_correct and incentive_reason_correct:
                self.log_test("Company Incentive Fields Storage", True, f"Amount: ₹{response1['incentive_amount']}, Reason: {response1['incentive_reason']}")
            else:
                self.log_test("Company Incentive Fields Storage", False, f"Amount: {response1.get('incentive_amount')}, Reason: {response1.get('incentive_reason')}")
        
        # Test 2: Test financial calculation includes incentive for company orders
        if incentive_order_id:
            success2, response2 = self.run_test("Company Order Financials with Incentive", "GET", f"orders/{incentive_order_id}/financials", 200)
            
            if success2 and response2:
                base_revenue = response2.get('base_revenue', 0)
                incentive_amount = response2.get('incentive_amount', 0)
                total_revenue = response2.get('total_revenue', 0)
                calculation_details = response2.get('calculation_details', '')
                
                # Expected: Kawale Cranes - Europ Assistance - Under-lift = Base 1500 + (45-40) * 15 = 1500 + 75 = 1575
                # Plus incentive: 1575 + 750 = 2325
                expected_base_rate = 1500.0
                expected_per_km = 15.0
                kms_travelled = 45.0
                excess_km = kms_travelled - 40.0  # 5km excess
                expected_base_revenue = expected_base_rate + (excess_km * expected_per_km)  # 1500 + (5 * 15) = 1575
                expected_incentive = 750.0
                expected_total = expected_base_revenue + expected_incentive  # 1575 + 750 = 2325
                
                if (base_revenue == expected_base_revenue and 
                    incentive_amount == expected_incentive and 
                    total_revenue == expected_total and
                    "Incentive" in calculation_details):
                    self.log_test("Company Incentive Financial Calculation", True, f"Base: ₹{base_revenue}, Incentive: ₹{incentive_amount}, Total: ₹{total_revenue}")
                    success2 = True
                else:
                    self.log_test("Company Incentive Financial Calculation", False, f"Expected Base: ₹{expected_base_revenue}, Incentive: ₹{expected_incentive}, Total: ₹{expected_total}, Got Base: ₹{base_revenue}, Incentive: ₹{incentive_amount}, Total: ₹{total_revenue}")
                    success2 = False
            else:
                success2 = False
        else:
            success2 = False
        
        # Test 3: Company order without incentive (should work fine)
        company_order_no_incentive = {
            "customer_name": "Test Company No Incentive",
            "phone": "9876543297",
            "order_type": "company",
            "company_name": "Mondial",
            "company_service_type": "2 Wheeler Towing",
            "company_driver_details": "Dubey",
            "company_towing_vehicle": "Tata ACE",
            "name_of_firm": "Kawale Cranes",
            "case_id_file_number": "NOINC002",
            "company_trip_from": "Delhi",
            "company_trip_to": "Gurgaon",
            "company_kms_travelled": 35.0  # Within base distance
        }
        
        success3, response3 = self.run_test("Company Order without Incentive", "POST", "orders", 200, company_order_no_incentive)
        no_incentive_order_id = None
        if success3 and 'id' in response3:
            self.created_orders.append(response3['id'])
            no_incentive_order_id = response3['id']
            
            # Verify no incentive fields
            incentive_amount_null = response3.get('incentive_amount') is None
            incentive_reason_null = response3.get('incentive_reason') is None
            
            if incentive_amount_null and incentive_reason_null:
                self.log_test("Company No Incentive Fields", True, "Incentive fields correctly null when not provided")
            else:
                self.log_test("Company No Incentive Fields", False, f"Amount: {response3.get('incentive_amount')}, Reason: {response3.get('incentive_reason')}")
        
        # Test 4: Financial calculation for company order without incentive
        if no_incentive_order_id:
            success4, response4 = self.run_test("Company Order Financials without Incentive", "GET", f"orders/{no_incentive_order_id}/financials", 200)
            
            if success4 and response4:
                base_revenue = response4.get('base_revenue', 0)
                incentive_amount = response4.get('incentive_amount', 0)
                total_revenue = response4.get('total_revenue', 0)
                
                # Expected: Kawale Cranes - Mondial - 2 Wheeler Towing = Base 1200 (within 40km)
                expected_base_revenue = 1200.0
                expected_incentive = 0.0
                expected_total = expected_base_revenue  # 1200 + 0 = 1200
                
                if (base_revenue == expected_base_revenue and 
                    incentive_amount == expected_incentive and 
                    total_revenue == expected_total):
                    self.log_test("Company No Incentive Financial Calculation", True, f"Base: ₹{base_revenue}, Total: ₹{total_revenue}")
                    success4 = True
                else:
                    self.log_test("Company No Incentive Financial Calculation", False, f"Expected Base: ₹{expected_base_revenue}, Total: ₹{expected_total}, Got Base: ₹{base_revenue}, Total: ₹{total_revenue}")
                    success4 = False
            else:
                success4 = False
        else:
            success4 = False
        
        all_passed = success1 and success2 and success3 and success4
        
        if all_passed:
            self.log_test("Company Incentive Functionality Overall", True, "All company incentive functionality tests passed")
        else:
            failed_tests = []
            if not success1: failed_tests.append("Incentive Storage")
            if not success2: failed_tests.append("Incentive Financial Calc")
            if not success3: failed_tests.append("No Incentive Order")
            if not success4: failed_tests.append("No Incentive Financial Calc")
            
            self.log_test("Company Incentive Functionality Overall", False, f"Failed tests: {', '.join(failed_tests)}")
        
        return all_passed

    def test_existing_functionality_preservation(self):
        """Test that existing functionality still works after mandatory fields changes"""
        print("\n🔄 Testing Existing Functionality Preservation...")
        
        # Test 1: Cash order creation (should not be affected by company mandatory fields)
        cash_order = {
            "customer_name": "Test Cash Preservation",
            "phone": "9876543298",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune",
            "cash_vehicle_name": "Tata ACE",
            "cash_service_type": "2 Wheeler Towing",
            "amount_received": 4500.0,
            "advance_amount": 1000.0,
            "cash_kms_travelled": 120.0,
            "cash_toll": 300.0,
            "cash_diesel": 800.0
        }
        
        success1, response1 = self.run_test("Cash Order Creation Preservation", "POST", "orders", 200, cash_order)
        if success1 and 'id' in response1:
            self.created_orders.append(response1['id'])
        
        # Test 2: Revenue calculation for existing orders (should work)
        success2, _ = self.run_test("Get Orders Summary Preservation", "GET", "orders/stats/summary", 200)
        
        # Test 3: Authentication still works
        success3, _ = self.run_test("Authentication Preservation", "GET", "auth/me", 200)
        
        # Test 4: Role-based access control still works
        success4, _ = self.run_test("RBAC Preservation", "GET", "users", 200)
        
        all_passed = success1 and success2 and success3 and success4
        
        if all_passed:
            self.log_test("Existing Functionality Preservation Overall", True, "All existing functionality preserved")
        else:
            failed_tests = []
            if not success1: failed_tests.append("Cash Order Creation")
            if not success2: failed_tests.append("Revenue Calculation")
            if not success3: failed_tests.append("Authentication")
            if not success4: failed_tests.append("RBAC")
            
            self.log_test("Existing Functionality Preservation Overall", False, f"Failed tests: {', '.join(failed_tests)}")
        
        return all_passed

    def test_mandatory_fields_and_incentives_comprehensive(self):
        """Comprehensive test of mandatory fields and incentive functionality"""
        print("\n🎯 COMPREHENSIVE MANDATORY FIELDS & INCENTIVES TESTING")
        print("=" * 60)
        
        # Test mandatory fields validation
        mandatory_fields_passed = self.test_mandatory_fields_validation()
        
        # Test incentive functionality for company orders
        incentive_functionality_passed = self.test_incentive_functionality_company_orders()
        
        # Test existing functionality preservation
        existing_functionality_passed = self.test_existing_functionality_preservation()
        
        # Overall result
        all_comprehensive_passed = mandatory_fields_passed and incentive_functionality_passed and existing_functionality_passed
        
        if all_comprehensive_passed:
            self.log_test("MANDATORY FIELDS & INCENTIVES COMPREHENSIVE", True, "✅ All mandatory fields and incentive tests passed successfully")
        else:
            failed_areas = []
            if not mandatory_fields_passed: failed_areas.append("Mandatory Fields Validation")
            if not incentive_functionality_passed: failed_areas.append("Incentive Functionality")
            if not existing_functionality_passed: failed_areas.append("Existing Functionality")
            
            self.log_test("MANDATORY FIELDS & INCENTIVES COMPREHENSIVE", False, f"❌ Failed areas: {', '.join(failed_areas)}")
        
        print("=" * 60)
        return all_comprehensive_passed

    def test_dashboard_orders_issue_focused(self):
        """Focused test for dashboard orders issue - Pydantic validation errors"""
        print("\n🎯 FOCUSED TEST: Dashboard Orders Issue (Pydantic Validation)")
        print("=" * 60)
        
        # Test 1: GET /api/orders - Check if it returns orders without Pydantic validation errors
        print("\n1. Testing GET /api/orders endpoint...")
        success1, response1 = self.run_test("Get All Orders (Dashboard)", "GET", "orders", 200)
        
        if success1 and response1:
            orders = response1 if isinstance(response1, list) else []
            self.log_test("Orders Retrieved Successfully", True, f"Retrieved {len(orders)} orders")
            
            # Check for both cash and company orders
            cash_orders = [o for o in orders if o.get('order_type') == 'cash']
            company_orders = [o for o in orders if o.get('order_type') == 'company']
            
            self.log_test("Cash Orders Present", len(cash_orders) > 0, f"Found {len(cash_orders)} cash orders")
            self.log_test("Company Orders Present", len(company_orders) > 0, f"Found {len(company_orders)} company orders")
            
            # Check for Pydantic validation issues in company orders
            pydantic_issues = []
            for order in company_orders:
                # Check for None values in company fields that should be strings
                company_fields = ['company_name', 'company_service_type', 'company_driver_details', 'company_towing_vehicle']
                for field in company_fields:
                    if field in order and order[field] is None:
                        pydantic_issues.append(f"Order {order.get('id', 'unknown')[:8]}: {field} is None")
            
            if pydantic_issues:
                self.log_test("Pydantic Validation Check", False, f"Found issues: {'; '.join(pydantic_issues[:3])}")
            else:
                self.log_test("Pydantic Validation Check", True, "No None values found in company string fields")
        else:
            self.log_test("Orders Retrieved Successfully", False, "Failed to retrieve orders")
        
        # Test 2: GET /api/orders with filters
        print("\n2. Testing filtered orders endpoints...")
        success2, _ = self.run_test("Filter by Cash Orders", "GET", "orders", 200, params={"order_type": "cash"})
        success3, _ = self.run_test("Filter by Company Orders", "GET", "orders", 200, params={"order_type": "company"})
        
        # Test 3: GET /api/orders/stats/summary
        print("\n3. Testing orders stats endpoint...")
        success4, stats_response = self.run_test("Get Orders Stats Summary", "GET", "orders/stats/summary", 200)
        
        if success4 and stats_response:
            total_orders = stats_response.get('total_orders', 0)
            by_type = stats_response.get('by_type', [])
            self.log_test("Stats Summary Working", True, f"Total orders: {total_orders}, Types: {len(by_type)}")
        else:
            self.log_test("Stats Summary Working", False, "Stats endpoint failed")
        
        # Test 4: Create a company order to test validation
        print("\n4. Testing company order creation (mandatory fields)...")
        company_order_test = {
            "customer_name": "Dashboard Test Company",
            "phone": "9876543999",
            "order_type": "company",
            "company_name": "Europ Assistance",
            "company_service_type": "2 Wheeler Towing",
            "company_driver_details": "Rahul",
            "company_towing_vehicle": "Tata ACE",
            "case_id_file_number": "DASH001"
        }
        
        success5, create_response = self.run_test("Create Company Order (Dashboard Test)", "POST", "orders", 200, company_order_test)
        if success5 and create_response and 'id' in create_response:
            self.created_orders.append(create_response['id'])
            
            # Verify the created order doesn't have None values
            company_fields = ['company_name', 'company_service_type', 'company_driver_details', 'company_towing_vehicle']
            all_fields_valid = True
            for field in company_fields:
                if create_response.get(field) is None or create_response.get(field) == '':
                    all_fields_valid = False
                    break
            
            self.log_test("Created Order Validation", all_fields_valid, "Company order created with valid mandatory fields")
        
        # Overall dashboard test result
        overall_success = success1 and success2 and success3 and success4 and success5
        
        if overall_success:
            self.log_test("🎯 DASHBOARD ORDERS ISSUE TEST", True, "All dashboard orders tests passed - no Pydantic validation errors detected")
        else:
            failed_tests = []
            if not success1: failed_tests.append("Get Orders")
            if not success2: failed_tests.append("Filter Cash")
            if not success3: failed_tests.append("Filter Company")
            if not success4: failed_tests.append("Stats Summary")
            if not success5: failed_tests.append("Create Company Order")
            
            self.log_test("🎯 DASHBOARD ORDERS ISSUE TEST", False, f"Failed tests: {', '.join(failed_tests)}")
        
        return overall_success

    def run_focused_dashboard_test(self):
        """Run focused test for dashboard orders issue"""
        print("🎯 FOCUSED DASHBOARD ORDERS TEST")
        print(f"🌐 Testing against: {self.api_url}")
        print("=" * 60)
        
        # Login first
        if not self.test_login():
            print("❌ Login failed. Cannot proceed with authenticated tests.")
            return False
        
        # Run focused dashboard test
        dashboard_success = self.test_dashboard_orders_issue_focused()
        
        # Cleanup any created orders
        self.cleanup_created_orders()
        
        # Print focused summary
        print("\n" + "=" * 60)
        print(f"🎯 FOCUSED TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL FOCUSED TESTS PASSED - Dashboard orders issue appears to be resolved!")
        else:
            print("❌ Some tests failed - Dashboard orders issue may still exist")
        
        return dashboard_success

    def test_dashboard_orders_loading(self):
        """Test dashboard orders loading without Pydantic validation errors - Priority 1"""
        print("\n🎯 Testing Dashboard Orders Loading (Priority 1)...")
        
        # Test 1: GET /api/orders - Verify orders load without Pydantic validation errors
        success1, response1 = self.run_test("Dashboard Orders Loading", "GET", "orders", 200)
        
        orders_count = 0
        if success1 and response1:
            orders = response1 if isinstance(response1, list) else []
            orders_count = len(orders)
            self.log_test("Orders Count Check", True, f"Retrieved {orders_count} orders successfully")
        
        # Test 2: Test filtered orders - cash orders
        success2, response2 = self.run_test("Dashboard Filter Cash Orders", "GET", "orders", 200, params={"order_type": "cash"})
        
        cash_count = 0
        if success2 and response2:
            cash_orders = response2 if isinstance(response2, list) else []
            cash_count = len(cash_orders)
            self.log_test("Cash Orders Filter", True, f"Retrieved {cash_count} cash orders")
        
        # Test 3: Test filtered orders - company orders
        success3, response3 = self.run_test("Dashboard Filter Company Orders", "GET", "orders", 200, params={"order_type": "company"})
        
        company_count = 0
        if success3 and response3:
            company_orders = response3 if isinstance(response3, list) else []
            company_count = len(company_orders)
            self.log_test("Company Orders Filter", True, f"Retrieved {company_count} company orders")
        
        # Test 4: Test stats endpoint
        success4, response4 = self.run_test("Dashboard Stats Summary", "GET", "orders/stats/summary", 200)
        
        if success4 and response4:
            total_orders = response4.get('total_orders', 0)
            by_type = response4.get('by_type', [])
            self.log_test("Stats Endpoint Verification", True, f"Total orders: {total_orders}, By type: {len(by_type)} categories")
        
        return success1 and success2 and success3 and success4

    def test_rates_management_endpoints(self):
        """Test rates management endpoints - Priority 2"""
        print("\n🎯 Testing Rates Management Endpoints (Priority 2)...")
        
        # Test 1: GET /api/rates - Test retrieving all service rates (Admin only)
        success1, response1 = self.run_test("Get All Service Rates", "GET", "rates", 200)
        
        rates_list = []
        rate_id_for_update = None
        if success1 and response1:
            rates_list = response1 if isinstance(response1, list) else []
            if rates_list:
                rate_id_for_update = rates_list[0].get('id')
                self.log_test("Rates Retrieval", True, f"Retrieved {len(rates_list)} service rates")
            else:
                self.log_test("Rates Retrieval", False, "No service rates found")
        
        if not rate_id_for_update:
            self.log_test("Rates Management Tests", False, "No rate ID available for update tests")
            return False
        
        # Test 2: PUT /api/rates/{rate_id} - Test updating rate fields
        update_data = {
            "base_rate": 1500.0,
            "base_distance_km": 45.0,
            "rate_per_km_beyond": 18.0
        }
        
        success2, response2 = self.run_test("Update Service Rate", "PUT", f"rates/{rate_id_for_update}", 200, update_data)
        
        if success2 and response2:
            updated_base_rate = response2.get('base_rate')
            updated_base_distance = response2.get('base_distance_km')
            updated_per_km = response2.get('rate_per_km_beyond')
            
            if (updated_base_rate == 1500.0 and 
                updated_base_distance == 45.0 and 
                updated_per_km == 18.0):
                self.log_test("Rate Update Verification", True, f"Base: ₹{updated_base_rate}, Distance: {updated_base_distance}km, Per km: ₹{updated_per_km}")
            else:
                self.log_test("Rate Update Verification", False, f"Update failed - Base: {updated_base_rate}, Distance: {updated_base_distance}, Per km: {updated_per_km}")
        
        # Test 3: Rate validation - Test invalid rate updates (negative values)
        invalid_update_data = {
            "base_rate": -100.0,  # Negative value should fail
            "rate_per_km_beyond": -5.0
        }
        
        success3, response3 = self.run_test("Invalid Rate Update (Negative Values)", "PUT", f"rates/{rate_id_for_update}", 400, invalid_update_data)
        
        # Test 4: Rate validation - Test missing fields
        incomplete_update_data = {
            "invalid_field": 123  # Invalid field should be ignored
        }
        
        success4, response4 = self.run_test("Invalid Rate Update (Invalid Fields)", "PUT", f"rates/{rate_id_for_update}", 400, incomplete_update_data)
        
        # Test 5: Audit trail verification - Check if rate updates are logged
        success5, response5 = self.run_test("Audit Trail for Rate Updates", "GET", "audit-logs", 200, params={"resource_type": "SERVICE_RATE", "action": "UPDATE"})
        
        audit_found = False
        if success5 and response5:
            audit_logs = response5 if isinstance(response5, list) else []
            # Look for recent rate update audit logs
            for log in audit_logs:
                if (log.get('resource_type') == 'SERVICE_RATE' and 
                    log.get('action') == 'UPDATE' and 
                    log.get('resource_id') == rate_id_for_update):
                    audit_found = True
                    break
            
            if audit_found:
                self.log_test("Rate Update Audit Trail", True, f"Found audit log for rate update")
            else:
                self.log_test("Rate Update Audit Trail", False, f"No audit log found for rate update")
        
        return success1 and success2 and success3 and success4 and (success5 and audit_found)

    def test_review_request_priorities(self):
        """Test the specific review request priorities"""
        print("\n🎯 TESTING REVIEW REQUEST PRIORITIES")
        print("=" * 60)
        
        # Priority 1: Dashboard Orders Loading
        priority1_success = self.test_dashboard_orders_loading()
        
        # Priority 2: Rates Management Endpoints  
        priority2_success = self.test_rates_management_endpoints()
        
        # Overall review request success
        overall_success = priority1_success and priority2_success
        
        if overall_success:
            self.log_test("Review Request Overall", True, "Both Priority 1 (Dashboard Orders) and Priority 2 (Rates Management) tests passed")
        else:
            failed_priorities = []
            if not priority1_success:
                failed_priorities.append("Priority 1 (Dashboard Orders)")
            if not priority2_success:
                failed_priorities.append("Priority 2 (Rates Management)")
            
            self.log_test("Review Request Overall", False, f"Failed priorities: {', '.join(failed_priorities)}")
        
        return overall_success

    def test_monthly_reports_system(self):
        """Test the new monthly reports system comprehensively"""
        print("\n📊 Testing Monthly Reports System...")
        
        # First create some test data for October 2024
        self.create_test_data_for_reports()
        
        # Test expense report by driver
        expense_report_success = self.test_expense_report_by_driver()
        
        # Test revenue report by vehicle type
        revenue_report_success = self.test_revenue_report_by_vehicle_type()
        
        # Test Excel export functionality
        excel_export_success = self.test_excel_export_functionality()
        
        # Test access control
        access_control_success = self.test_reports_access_control()
        
        # Test edge cases
        edge_cases_success = self.test_reports_edge_cases()
        
        all_passed = all([
            expense_report_success, revenue_report_success, 
            excel_export_success, access_control_success, edge_cases_success
        ])
        
        if all_passed:
            self.log_test("Monthly Reports System Overall", True, "All monthly reports tests passed")
        else:
            failed_tests = []
            if not expense_report_success: failed_tests.append("Expense Report")
            if not revenue_report_success: failed_tests.append("Revenue Report")
            if not excel_export_success: failed_tests.append("Excel Export")
            if not access_control_success: failed_tests.append("Access Control")
            if not edge_cases_success: failed_tests.append("Edge Cases")
            
            self.log_test("Monthly Reports System Overall", False, f"Failed tests: {', '.join(failed_tests)}")
        
        return all_passed

    def create_test_data_for_reports(self):
        """Create test data for October 2024 reports"""
        print("\n📝 Creating Test Data for Reports...")
        
        from datetime import datetime, timezone
        
        # Create cash orders with different drivers and expenses
        cash_orders = [
            {
                "customer_name": "Report Test Cash 1",
                "phone": "9876540001",
                "order_type": "cash",
                "date_time": datetime(2024, 10, 15, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "cash_driver_name": "Rahul",
                "cash_service_type": "2 Wheeler Towing",
                "cash_vehicle_name": "Honda Activa",
                "amount_received": 2500.0,
                "cash_diesel": 300.0,
                "cash_toll": 150.0
            },
            {
                "customer_name": "Report Test Cash 2", 
                "phone": "9876540002",
                "order_type": "cash",
                "date_time": datetime(2024, 10, 20, 14, 30, 0, tzinfo=timezone.utc).isoformat(),
                "cash_driver_name": "Subhash",
                "cash_service_type": "Under-lift",
                "cash_vehicle_name": "Tata ACE",
                "amount_received": 4000.0,
                "cash_diesel": 500.0,
                "cash_toll": 200.0,
                "incentive_amount": 300.0,
                "incentive_reason": "Quick service"
            }
        ]
        
        # Create company orders with different service types and calculations
        company_orders = [
            {
                "customer_name": "Report Test Company 1",
                "phone": "9876540003",
                "order_type": "company",
                "date_time": datetime(2024, 10, 10, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
                "name_of_firm": "Kawale Cranes",
                "company_name": "Europ Assistance",
                "company_service_type": "2 Wheeler Towing",
                "company_driver_name": "Dubey",
                "company_driver_details": "Dubey",
                "company_towing_vehicle": "Honda Activa",
                "company_kms_travelled": 35.0,  # Within base distance
                "company_diesel": 250.0,
                "company_toll": 100.0,
                "case_id_file_number": "RPT001"
            },
            {
                "customer_name": "Report Test Company 2",
                "phone": "9876540004", 
                "order_type": "company",
                "date_time": datetime(2024, 10, 25, 16, 45, 0, tzinfo=timezone.utc).isoformat(),
                "name_of_firm": "Vidharbha Towing",
                "company_name": "TVS",
                "company_service_type": "Under-lift",
                "company_driver_name": "Sudhir",
                "company_driver_details": "Sudhir",
                "company_towing_vehicle": "Tata ACE",
                "company_kms_travelled": 65.0,  # Beyond base distance
                "company_diesel": 600.0,
                "company_toll": 250.0,
                "incentive_amount": 500.0,
                "incentive_reason": "Complex case handled well",
                "case_id_file_number": "RPT002"
            },
            {
                "customer_name": "Report Test Company 3",
                "phone": "9876540005",
                "order_type": "company", 
                "date_time": datetime(2024, 10, 28, 11, 15, 0, tzinfo=timezone.utc).isoformat(),
                "name_of_firm": "Kawale Cranes",
                "company_name": "Mondial",
                "company_service_type": "FBT",
                "company_driver_name": "Vikas",
                "company_driver_details": "Vikas",
                "company_towing_vehicle": "Mahindra Bolero",
                "company_kms_travelled": 45.0,  # Beyond base distance
                "company_diesel": 400.0,
                "company_toll": 180.0,
                "case_id_file_number": "RPT003"
            }
        ]
        
        # Create all test orders
        created_count = 0
        for order_data in cash_orders + company_orders:
            success, response = self.run_test(f"Create Report Test Order {created_count + 1}", "POST", "orders", 200, order_data)
            if success and response and 'id' in response:
                self.created_orders.append(response['id'])
                created_count += 1
        
        self.log_test("Test Data Creation", True, f"Created {created_count} test orders for October 2024")
        return created_count > 0

    def test_expense_report_by_driver(self):
        """Test GET /api/reports/expense-by-driver endpoint"""
        print("\n💰 Testing Expense Report by Driver...")
        
        # Test basic expense report for October 2024
        success1, response1 = self.run_test(
            "Expense Report October 2024",
            "GET",
            "reports/expense-by-driver",
            200,
            params={"month": 10, "year": 2024}
        )
        
        if success1 and response1:
            # Verify response structure
            required_fields = ["month", "year", "report_type", "data", "summary"]
            has_all_fields = all(field in response1 for field in required_fields)
            
            if has_all_fields:
                self.log_test("Expense Report Structure", True, "Response has all required fields")
                
                # Verify report type
                if response1.get("report_type") == "expense_by_driver":
                    self.log_test("Expense Report Type", True, "Correct report type")
                    
                    # Verify data aggregation
                    data = response1.get("data", [])
                    if data and len(data) > 0:
                        # Check driver data structure
                        sample_driver = data[0]
                        driver_fields = ["driver_name", "cash_orders", "company_orders", "total_orders", 
                                       "total_diesel_expense", "total_toll_expense", "total_expenses"]
                        
                        if all(field in sample_driver for field in driver_fields):
                            self.log_test("Driver Data Structure", True, f"Driver data has all required fields")
                            
                            # Verify expense calculations (diesel + toll)
                            for driver in data:
                                expected_total = driver["total_diesel_expense"] + driver["total_toll_expense"]
                                if driver["total_expenses"] == expected_total:
                                    self.log_test(f"Expense Calc for {driver['driver_name']}", True, 
                                                f"Total: ₹{driver['total_expenses']} (Diesel: ₹{driver['total_diesel_expense']}, Toll: ₹{driver['total_toll_expense']})")
                                else:
                                    self.log_test(f"Expense Calc for {driver['driver_name']}", False,
                                                f"Expected: ₹{expected_total}, Got: ₹{driver['total_expenses']}")
                            
                            # Test different month to verify date filtering
                            success2, response2 = self.run_test(
                                "Expense Report September 2024",
                                "GET", 
                                "reports/expense-by-driver",
                                200,
                                params={"month": 9, "year": 2024}
                            )
                            
                            if success2:
                                self.log_test("Date Filtering Test", True, "Different month query successful")
                                return True
                        else:
                            self.log_test("Driver Data Structure", False, f"Missing fields in driver data")
                    else:
                        self.log_test("Expense Report Data", False, "No driver data returned")
                else:
                    self.log_test("Expense Report Type", False, f"Expected 'expense_by_driver', got '{response1.get('report_type')}'")
            else:
                self.log_test("Expense Report Structure", False, f"Missing fields: {set(required_fields) - set(response1.keys())}")
        
        return False

    def test_revenue_report_by_vehicle_type(self):
        """Test GET /api/reports/revenue-by-vehicle-type endpoint"""
        print("\n💰 Testing Revenue Report by Vehicle Type...")
        
        # Test basic revenue report for October 2024
        success1, response1 = self.run_test(
            "Revenue Report October 2024",
            "GET",
            "reports/revenue-by-vehicle-type", 
            200,
            params={"month": 10, "year": 2024}
        )
        
        if success1 and response1:
            # Verify response structure
            required_fields = ["month", "year", "report_type", "data", "summary"]
            has_all_fields = all(field in response1 for field in required_fields)
            
            if has_all_fields:
                self.log_test("Revenue Report Structure", True, "Response has all required fields")
                
                # Verify report type
                if response1.get("report_type") == "revenue_by_vehicle_type":
                    self.log_test("Revenue Report Type", True, "Correct report type")
                    
                    # Verify data aggregation
                    data = response1.get("data", [])
                    if data and len(data) > 0:
                        # Check service type data structure
                        sample_service = data[0]
                        service_fields = ["service_type", "cash_orders", "company_orders", "total_orders",
                                        "total_base_revenue", "total_incentive_amount", "total_revenue"]
                        
                        if all(field in sample_service for field in service_fields):
                            self.log_test("Service Type Data Structure", True, "Service data has all required fields")
                            
                            # Verify revenue calculations (base + incentive)
                            for service in data:
                                expected_total = service["total_base_revenue"] + service["total_incentive_amount"]
                                if service["total_revenue"] == expected_total:
                                    self.log_test(f"Revenue Calc for {service['service_type']}", True,
                                                f"Total: ₹{service['total_revenue']} (Base: ₹{service['total_base_revenue']}, Incentive: ₹{service['total_incentive_amount']})")
                                else:
                                    self.log_test(f"Revenue Calc for {service['service_type']}", False,
                                                f"Expected: ₹{expected_total}, Got: ₹{service['total_revenue']}")
                            
                            # Verify that cash orders use amount_received and company orders use SK rates
                            cash_service = next((s for s in data if s["cash_orders"] > 0), None)
                            company_service = next((s for s in data if s["company_orders"] > 0), None)
                            
                            if cash_service:
                                self.log_test("Cash Order Revenue Logic", True, f"Cash orders found in {cash_service['service_type']}")
                            
                            if company_service:
                                self.log_test("Company Order Revenue Logic", True, f"Company orders found in {company_service['service_type']}")
                            
                            return True
                        else:
                            self.log_test("Service Type Data Structure", False, "Missing fields in service data")
                    else:
                        self.log_test("Revenue Report Data", False, "No service type data returned")
                else:
                    self.log_test("Revenue Report Type", False, f"Expected 'revenue_by_vehicle_type', got '{response1.get('report_type')}'")
            else:
                self.log_test("Revenue Report Structure", False, f"Missing fields: {set(required_fields) - set(response1.keys())}")
        
        return False

    def test_excel_export_functionality(self):
        """Test Excel export endpoints for reports"""
        print("\n📊 Testing Excel Export Functionality...")
        
        # Test expense report Excel export
        success1, response1 = self.run_test(
            "Export Expense Report Excel",
            "GET",
            "reports/expense-by-driver/export",
            200,
            params={"month": 10, "year": 2024}
        )
        
        # Test revenue report Excel export
        success2, response2 = self.run_test(
            "Export Revenue Report Excel", 
            "GET",
            "reports/revenue-by-vehicle-type/export",
            200,
            params={"month": 10, "year": 2024}
        )
        
        # Note: We can't easily verify Excel file content in this test framework,
        # but we can verify that the endpoints return successful responses
        if success1 and success2:
            self.log_test("Excel Export Functionality", True, "Both Excel export endpoints working")
            return True
        else:
            failed_exports = []
            if not success1: failed_exports.append("Expense Report")
            if not success2: failed_exports.append("Revenue Report")
            self.log_test("Excel Export Functionality", False, f"Failed exports: {', '.join(failed_exports)}")
        
        return False

    def test_reports_access_control(self):
        """Test that only Admin/Super Admin can access report endpoints"""
        print("\n🔐 Testing Reports Access Control...")
        
        # Create a data entry user for testing
        data_entry_user = {
            "email": "reporttest@kawalecranes.com",
            "full_name": "Report Test User",
            "password": "reporttest123",
            "role": "data_entry"
        }
        
        success1, create_response = self.run_test("Create Data Entry User for Reports", "POST", "auth/register", 200, data_entry_user)
        
        if success1 and create_response:
            # Login as data entry user
            success2, login_response = self.run_test(
                "Data Entry Login for Reports",
                "POST",
                "auth/login",
                200,
                data={"email": "reporttest@kawalecranes.com", "password": "reporttest123"}
            )
            
            if success2 and 'access_token' in login_response:
                old_token = self.token
                self.token = login_response['access_token']
                
                # Test that data entry user cannot access reports (should get 403)
                success3, _ = self.run_test(
                    "Data Entry Access Expense Report (Should Fail)",
                    "GET",
                    "reports/expense-by-driver",
                    403,
                    params={"month": 10, "year": 2024}
                )
                
                success4, _ = self.run_test(
                    "Data Entry Access Revenue Report (Should Fail)",
                    "GET", 
                    "reports/revenue-by-vehicle-type",
                    403,
                    params={"month": 10, "year": 2024}
                )
                
                success5, _ = self.run_test(
                    "Data Entry Access Excel Export (Should Fail)",
                    "GET",
                    "reports/expense-by-driver/export",
                    403,
                    params={"month": 10, "year": 2024}
                )
                
                # Restore admin token
                self.token = old_token
                
                # Test that admin can access reports (should get 200)
                success6, _ = self.run_test(
                    "Admin Access Expense Report",
                    "GET",
                    "reports/expense-by-driver", 
                    200,
                    params={"month": 10, "year": 2024}
                )
                
                # Cleanup - delete test user
                if 'id' in create_response:
                    self.run_test("Cleanup Report Test User", "DELETE", f"users/{create_response['id']}", 200)
                
                if all([success3, success4, success5, success6]):
                    self.log_test("Reports Access Control", True, "Proper role-based access control working")
                    return True
                else:
                    self.log_test("Reports Access Control", False, "Access control not working properly")
        
        return False

    def test_reports_edge_cases(self):
        """Test edge cases for reports"""
        print("\n🧪 Testing Reports Edge Cases...")
        
        # Test with month that has no data (e.g., January 2024)
        success1, response1 = self.run_test(
            "Expense Report No Data Month",
            "GET",
            "reports/expense-by-driver",
            200,
            params={"month": 1, "year": 2024}
        )
        
        if success1 and response1:
            data = response1.get("data", [])
            summary = response1.get("summary", {})
            
            # Should return empty data but valid structure
            if len(data) == 0 and summary.get("total_drivers") == 0:
                self.log_test("No Data Month Handling", True, "Correctly handles months with no data")
            else:
                self.log_test("No Data Month Handling", False, f"Expected empty data, got {len(data)} drivers")
        
        # Test invalid month parameter
        success2, response2 = self.run_test(
            "Invalid Month Parameter",
            "GET",
            "reports/expense-by-driver",
            422,  # Validation error
            params={"month": 13, "year": 2024}
        )
        
        # Test invalid year parameter
        success3, response3 = self.run_test(
            "Invalid Year Parameter",
            "GET",
            "reports/revenue-by-vehicle-type",
            422,  # Validation error
            params={"month": 10, "year": 2050}
        )
        
        # Test missing parameters
        success4, response4 = self.run_test(
            "Missing Month Parameter",
            "GET",
            "reports/expense-by-driver",
            422,  # Validation error
            params={"year": 2024}
        )
        
        success5, response5 = self.run_test(
            "Missing Year Parameter", 
            "GET",
            "reports/revenue-by-vehicle-type",
            422,  # Validation error
            params={"month": 10}
        )
        
        if all([success1, success2, success3, success4, success5]):
            self.log_test("Reports Edge Cases", True, "All edge cases handled correctly")
            return True
        else:
            failed_cases = []
            if not success1: failed_cases.append("No Data Month")
            if not success2: failed_cases.append("Invalid Month")
            if not success3: failed_cases.append("Invalid Year")
            if not success4: failed_cases.append("Missing Month")
            if not success5: failed_cases.append("Missing Year")
            
            self.log_test("Reports Edge Cases", False, f"Failed cases: {', '.join(failed_cases)}")
        
        return False

    def test_new_reporting_features(self):
        """Test new reporting features as requested in review"""
        print("\n📊 Testing New Reporting Features...")
        
        # Create test data for October 2024
        test_orders = []
        
        # Create orders with different towing vehicles for revenue by towing vehicle report
        towing_vehicles_data = [
            {
                "customer_name": "Revenue Test User 1",
                "phone": "9876540001",
                "order_type": "cash",
                "date_time": "2024-10-15T10:00:00Z",
                "cash_towing_vehicle": "Tata ACE",
                "cash_driver_name": "Rahul",
                "cash_service_type": "2-Wheeler Crane",
                "amount_received": 3000.0,
                "incentive_amount": 200.0,
                "incentive_reason": "Quick service"
            },
            {
                "customer_name": "Revenue Test User 2", 
                "phone": "9876540002",
                "order_type": "company",
                "date_time": "2024-10-20T14:30:00Z",
                "company_towing_vehicle": "Mahindra Bolero",
                "company_driver_name": "Subhash",
                "name_of_firm": "Kawale Cranes",
                "company_name": "Europ Assistance",
                "company_service_type": "2 Wheeler Towing",
                "company_kms_travelled": 35.0,
                "case_id_file_number": "REV001"
            },
            {
                "customer_name": "Revenue Test User 3",
                "phone": "9876540003", 
                "order_type": "cash",
                "date_time": "2024-10-25T16:45:00Z",
                "cash_towing_vehicle": "Tata ACE",
                "cash_driver_name": "Dubey",
                "cash_service_type": "4-Wheeler Crane",
                "amount_received": 5000.0
            }
        ]
        
        # Create the test orders
        created_order_ids = []
        for i, order_data in enumerate(towing_vehicles_data):
            success, response = self.run_test(f"Create Test Order {i+1} for Reports", "POST", "orders", 200, order_data)
            if success and response and 'id' in response:
                created_order_ids.append(response['id'])
                self.created_orders.append(response['id'])
        
        # Test 1: Revenue by Towing Vehicle Report
        success1, response1 = self.run_test(
            "Revenue by Towing Vehicle Report (Oct 2024)",
            "GET", 
            "reports/revenue-by-towing-vehicle",
            200,
            params={"month": 10, "year": 2024}
        )
        
        if success1 and response1:
            data = response1.get("data", [])
            if len(data) > 0:
                # Check if we have Tata ACE and Mahindra Bolero in results
                towing_vehicles = [item.get("towing_vehicle") for item in data]
                if "Tata ACE" in towing_vehicles and "Mahindra Bolero" in towing_vehicles:
                    self.log_test("Revenue by Towing Vehicle Data", True, f"Found vehicles: {towing_vehicles}")
                else:
                    self.log_test("Revenue by Towing Vehicle Data", False, f"Expected Tata ACE and Mahindra Bolero, got: {towing_vehicles}")
            else:
                self.log_test("Revenue by Towing Vehicle Data", False, "No data returned")
        
        # Test 2: Revenue by Towing Vehicle Excel Export
        success2, response2 = self.run_test(
            "Revenue by Towing Vehicle Excel Export",
            "GET",
            "reports/revenue-by-towing-vehicle/export", 
            200,
            params={"month": 10, "year": 2024}
        )
        
        # Test 3: Custom Reports with different group_by options
        custom_report_configs = [
            {
                "start_date": "2024-10-01T00:00:00Z",
                "end_date": "2024-10-31T23:59:59Z", 
                "group_by": "driver",
                "report_type": "summary"
            },
            {
                "start_date": "2024-10-01T00:00:00Z",
                "end_date": "2024-10-31T23:59:59Z",
                "group_by": "service_type", 
                "report_type": "summary"
            },
            {
                "start_date": "2024-10-01T00:00:00Z",
                "end_date": "2024-10-31T23:59:59Z",
                "group_by": "towing_vehicle",
                "report_type": "detailed"
            },
            {
                "start_date": "2024-10-01T00:00:00Z", 
                "end_date": "2024-10-31T23:59:59Z",
                "group_by": "firm",
                "report_type": "summary"
            },
            {
                "start_date": "2024-10-01T00:00:00Z",
                "end_date": "2024-10-31T23:59:59Z",
                "group_by": "company",
                "report_type": "summary"
            }
        ]
        
        custom_report_results = []
        for i, config in enumerate(custom_report_configs):
            success, response = self.run_test(
                f"Custom Report - Group by {config['group_by']}",
                "POST",
                "reports/custom",
                200,
                data=config
            )
            custom_report_results.append(success)
            
            if success and response:
                group_by = response.get("group_by")
                data = response.get("data", [])
                summary = response.get("summary", {})
                self.log_test(f"Custom Report {group_by} Data", True, f"Groups: {len(data)}, Total Orders: {summary.get('total_orders', 0)}")
        
        # Test 4: Custom Report Excel Export
        success4, response4 = self.run_test(
            "Custom Report Excel Export",
            "POST",
            "reports/custom/export",
            200,
            data=custom_report_configs[0]  # Use driver grouping
        )
        
        return success1 and success2 and all(custom_report_results) and success4

    def test_create_new_rates(self):
        """Test creating new service rates"""
        print("\n💰 Testing Create New Rates...")
        
        # Test 1: Create a new valid rate
        new_rate_data = {
            "name_of_firm": "Test Firm",
            "company_name": "Test Company", 
            "service_type": "Test Service",
            "base_rate": 1500.0,
            "base_distance_km": 45.0,
            "rate_per_km_beyond": 20.0
        }
        
        success1, response1 = self.run_test(
            "Create New Service Rate",
            "POST",
            "rates",
            200,
            data=new_rate_data
        )
        
        created_rate_id = None
        if success1 and response1:
            created_rate_id = response1.get('id')
            # Verify the created rate has correct values
            if (response1.get('base_rate') == 1500.0 and 
                response1.get('base_distance_km') == 45.0 and
                response1.get('rate_per_km_beyond') == 20.0):
                self.log_test("New Rate Values Verification", True, f"Rate created with correct values")
            else:
                self.log_test("New Rate Values Verification", False, f"Rate values mismatch")
        
        # Test 2: Try to create duplicate rate (should fail)
        success2, response2 = self.run_test(
            "Create Duplicate Rate (Should Fail)",
            "POST", 
            "rates",
            400,
            data=new_rate_data
        )
        
        if success2 and response2:
            detail = response2.get('detail', '')
            if 'already exists' in detail:
                self.log_test("Duplicate Rate Validation", True, f"Correctly rejected duplicate: {detail}")
            else:
                self.log_test("Duplicate Rate Validation", False, f"Unexpected error: {detail}")
        
        # Test 3: Create rate with missing required fields (should fail)
        invalid_rate_data = {
            "name_of_firm": "Invalid Firm",
            "company_name": "Invalid Company"
            # Missing service_type, base_rate, rate_per_km_beyond
        }
        
        success3, response3 = self.run_test(
            "Create Rate Missing Fields (Should Fail)",
            "POST",
            "rates", 
            400,
            data=invalid_rate_data
        )
        
        # Test 4: Verify audit trail for rate creation
        if created_rate_id:
            success4, response4 = self.run_test(
                "Check Audit Trail for Rate Creation",
                "GET",
                "audit-logs",
                200,
                params={"resource_type": "SERVICE_RATE", "action": "CREATE"}
            )
            
            if success4 and response4:
                logs = response4 if isinstance(response4, list) else []
                rate_creation_logs = [log for log in logs if log.get('resource_id') == created_rate_id]
                if rate_creation_logs:
                    self.log_test("Rate Creation Audit Trail", True, f"Found {len(rate_creation_logs)} audit log(s)")
                else:
                    self.log_test("Rate Creation Audit Trail", False, "No audit logs found for rate creation")
        
        # Cleanup: Delete the created rate
        if created_rate_id:
            self.run_test("Cleanup Created Rate", "DELETE", f"rates/{created_rate_id}", 200)
        
        return success1 and success2 and success3

    def test_excel_import_investigation(self):
        """Test dashboard display and investigate Excel import issues"""
        print("\n🔍 Testing Excel Import Investigation...")
        
        # Test 1: Get orders with various date filters
        date_filters = [
            {"start_date": "2024-01-01", "end_date": "2024-12-31"},  # Full year 2024
            {"start_date": "2023-01-01", "end_date": "2023-12-31"},  # Full year 2023
            {"start_date": "2024-10-01", "end_date": "2024-10-31"},  # October 2024
            {"start_date": "2024-11-01", "end_date": "2024-11-30"},  # November 2024
        ]
        
        orders_by_period = {}
        for i, date_filter in enumerate(date_filters):
            # Note: The orders endpoint doesn't have date filtering, so we'll get all orders
            # and check if there are orders from different time periods
            success, response = self.run_test(
                f"Get Orders for Period {i+1}",
                "GET",
                "orders",
                200,
                params={"limit": 1000}
            )
            
            if success and response:
                orders = response if isinstance(response, list) else []
                
                # Filter orders by date manually to check date distribution
                period_orders = []
                for order in orders:
                    order_date = order.get('date_time')
                    if order_date:
                        # Check if order falls within the period
                        if isinstance(order_date, str):
                            try:
                                order_datetime = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
                                start_datetime = datetime.fromisoformat(date_filter['start_date'] + 'T00:00:00+00:00')
                                end_datetime = datetime.fromisoformat(date_filter['end_date'] + 'T23:59:59+00:00')
                                
                                if start_datetime <= order_datetime <= end_datetime:
                                    period_orders.append(order)
                            except:
                                continue
                
                orders_by_period[f"period_{i+1}"] = len(period_orders)
                self.log_test(f"Orders in Period {i+1}", True, f"Found {len(period_orders)} orders in {date_filter['start_date']} to {date_filter['end_date']}")
        
        # Test 2: Check if orders appear in different months/years
        total_orders_found = sum(orders_by_period.values())
        if total_orders_found > 0:
            self.log_test("Orders Date Distribution", True, f"Total orders across periods: {total_orders_found}")
            
            # Check for orders in different periods
            periods_with_orders = sum(1 for count in orders_by_period.values() if count > 0)
            if periods_with_orders > 1:
                self.log_test("Multi-Period Orders", True, f"Orders found in {periods_with_orders} different periods")
            else:
                self.log_test("Multi-Period Orders", False, f"Orders only found in {periods_with_orders} period(s)")
        else:
            self.log_test("Orders Date Distribution", False, "No orders found in any period")
        
        # Test 3: Check reports for different months/years to find imported data
        report_periods = [
            {"month": 10, "year": 2024},
            {"month": 11, "year": 2024}, 
            {"month": 9, "year": 2024},
            {"month": 12, "year": 2023}
        ]
        
        reports_with_data = 0
        for period in report_periods:
            # Test expense report
            success1, response1 = self.run_test(
                f"Expense Report {period['month']}/{period['year']}",
                "GET",
                "reports/expense-by-driver",
                200,
                params=period
            )
            
            if success1 and response1:
                data = response1.get("data", [])
                if len(data) > 0:
                    reports_with_data += 1
                    self.log_test(f"Report Data {period['month']}/{period['year']}", True, f"Found {len(data)} driver records")
                else:
                    self.log_test(f"Report Data {period['month']}/{period['year']}", False, "No data in report")
            
            # Test revenue report
            success2, response2 = self.run_test(
                f"Revenue Report {period['month']}/{period['year']}",
                "GET", 
                "reports/revenue-by-towing-vehicle",
                200,
                params=period
            )
            
            if success2 and response2:
                data = response2.get("data", [])
                if len(data) > 0:
                    self.log_test(f"Revenue Report Data {period['month']}/{period['year']}", True, f"Found {len(data)} vehicle records")
        
        # Test 4: Investigate datetime parsing and storage format
        success4, response4 = self.run_test(
            "Sample Orders for DateTime Investigation",
            "GET",
            "orders",
            200,
            params={"limit": 10}
        )
        
        datetime_formats_found = set()
        if success4 and response4:
            orders = response4 if isinstance(response4, list) else []
            for order in orders[:5]:  # Check first 5 orders
                date_time = order.get('date_time')
                if date_time:
                    datetime_formats_found.add(type(date_time).__name__)
                    if isinstance(date_time, str):
                        # Check format patterns
                        if 'T' in date_time and 'Z' in date_time:
                            datetime_formats_found.add("ISO_with_Z")
                        elif 'T' in date_time and '+' in date_time:
                            datetime_formats_found.add("ISO_with_timezone")
                        else:
                            datetime_formats_found.add("other_string_format")
            
            self.log_test("DateTime Format Investigation", True, f"Found formats: {list(datetime_formats_found)}")
        
        return total_orders_found > 0 and reports_with_data > 0

    def test_excel_import_verification(self):
        """Test Excel import verification - PRIMARY FOCUS"""
        print("\n📥 Testing Excel Import Verification - PRIMARY FOCUS...")
        
        # Test 1: Dashboard Orders Loading - should return all imported records (205+ orders)
        success1, orders_response = self.run_test("Dashboard Orders Loading", "GET", "orders", 200, params={"limit": 1000})
        
        total_orders = 0
        if success1 and orders_response:
            total_orders = len(orders_response)
            if total_orders >= 205:
                self.log_test("Excel Import Count Verification", True, f"Found {total_orders} orders (expected >= 205)")
            else:
                self.log_test("Excel Import Count Verification", False, f"Found {total_orders} orders, expected >= 205")
        
        # Test 2: Order Count Verification via stats
        success2, stats_response = self.run_test("Order Count Stats", "GET", "orders/stats/summary", 200)
        
        cash_count = 0
        company_count = 0
        if success2 and stats_response:
            total_from_stats = stats_response.get('total_orders', 0)
            by_type = stats_response.get('by_type', [])
            
            for type_stat in by_type:
                if type_stat.get('_id') == 'cash':
                    cash_count = type_stat.get('count', 0)
                elif type_stat.get('_id') == 'company':
                    company_count = type_stat.get('count', 0)
            
            if cash_count >= 157 and company_count >= 48:
                self.log_test("Excel Import Stats Verification", True, f"Cash: {cash_count} (expected >= 157), Company: {company_count} (expected >= 48)")
            else:
                self.log_test("Excel Import Stats Verification", False, f"Cash: {cash_count}, Company: {company_count} - expected >= 157 cash, >= 48 company")
        
        # Test 3: Sample Record Verification - Cash order with Kartik
        success3, cash_orders = self.run_test("Sample Cash Record Search", "GET", "orders", 200, params={"order_type": "cash", "customer_name": "Kartik", "limit": 100})
        
        kartik_found = False
        if success3 and cash_orders:
            for order in cash_orders:
                if ("Kartik" in order.get('customer_name', '') and 
                    order.get('phone') == '7350009241' and
                    order.get('cash_driver_name') == 'Meshram' and
                    order.get('cash_service_type') == 'FBT' and
                    order.get('amount_received') == 2000.0):
                    kartik_found = True
                    self.log_test("Sample Cash Record Found", True, f"Found Kartik record: {order.get('customer_name')}, {order.get('phone')}")
                    break
        
        if not kartik_found:
            self.log_test("Sample Cash Record Found", False, "Could not find expected Kartik cash order record")
        
        # Test 4: Sample Record Verification - Company order with Sachi
        success4, company_orders = self.run_test("Sample Company Record Search", "GET", "orders", 200, params={"order_type": "company", "customer_name": "Sachi", "limit": 100})
        
        sachi_found = False
        if success4 and company_orders:
            for order in company_orders:
                if ("Sachi" in order.get('customer_name', '') and 
                    order.get('phone') == '9545617572' and
                    order.get('company_name') == 'Europ Assistance' and
                    order.get('company_service_type') == '2 Wheeler Towing'):
                    sachi_found = True
                    self.log_test("Sample Company Record Found", True, f"Found Sachi record: {order.get('customer_name')}, {order.get('company_name')}")
                    break
        
        if not sachi_found:
            self.log_test("Sample Company Record Found", False, "Could not find expected Sachi company order record")
        
        # Test 5: Date Filtering - September 2025 data
        success5, sept_orders = self.run_test("September 2025 Date Filter", "GET", "orders", 200, params={"limit": 1000})
        
        sept_2025_count = 0
        if success5 and sept_orders:
            for order in sept_orders:
                date_time = order.get('date_time', '')
                if '2025-09-' in str(date_time):
                    sept_2025_count += 1
            
            if sept_2025_count >= 200:  # Most imported records should be from Sept 2025
                self.log_test("September 2025 Data Verification", True, f"Found {sept_2025_count} orders from September 2025")
            else:
                self.log_test("September 2025 Data Verification", False, f"Found {sept_2025_count} orders from September 2025, expected more")
        
        # Test 6: Filtering by order type
        success6, cash_filter = self.run_test("Filter Cash Orders", "GET", "orders", 200, params={"order_type": "cash", "limit": 1000})
        success7, company_filter = self.run_test("Filter Company Orders", "GET", "orders", 200, params={"order_type": "company", "limit": 1000})
        
        cash_filter_count = len(cash_filter) if success6 and cash_filter else 0
        company_filter_count = len(company_filter) if success7 and company_filter else 0
        
        if cash_filter_count >= 157 and company_filter_count >= 48:
            self.log_test("Order Type Filtering", True, f"Cash filter: {cash_filter_count}, Company filter: {company_filter_count}")
        else:
            self.log_test("Order Type Filtering", False, f"Cash filter: {cash_filter_count}, Company filter: {company_filter_count}")
        
        return all([success1, success2, success3 or True, success4 or True, success5, success6, success7])  # Allow sample records to be optional
    
    def test_reports_with_imported_data(self):
        """Test reports integration with imported data"""
        print("\n📊 Testing Reports Integration with Imported Data...")
        
        # Test 1: Expense by Driver Report for September 2025
        success1, expense_report = self.run_test("Expense Report Sept 2025", "GET", "reports/expense-by-driver", 200, params={"month": 9, "year": 2025})
        
        drivers_found = []
        if success1 and expense_report:
            data = expense_report.get('data', [])
            for driver_data in data:
                driver_name = driver_data.get('driver_name', '')
                if driver_name in ['Meshram', 'Akshay', 'Vikas']:
                    drivers_found.append(driver_name)
            
            if len(drivers_found) >= 2:
                self.log_test("Imported Drivers in Expense Report", True, f"Found drivers: {', '.join(drivers_found)}")
            else:
                self.log_test("Imported Drivers in Expense Report", False, f"Only found drivers: {', '.join(drivers_found)}")
        
        # Test 2: Revenue by Vehicle Type Report for September 2025
        success2, revenue_report = self.run_test("Revenue Report Sept 2025", "GET", "reports/revenue-by-vehicle-type", 200, params={"month": 9, "year": 2025})
        
        service_types_found = []
        if success2 and revenue_report:
            data = revenue_report.get('data', [])
            for service_data in data:
                service_type = service_data.get('service_type', '')
                if service_type in ['FBT', '2 Wheeler Towing', 'Under-lift']:
                    service_types_found.append(service_type)
            
            if len(service_types_found) >= 2:
                self.log_test("Imported Service Types in Revenue Report", True, f"Found service types: {', '.join(service_types_found)}")
            else:
                self.log_test("Imported Service Types in Revenue Report", False, f"Only found service types: {', '.join(service_types_found)}")
        
        # Test 3: Revenue by Towing Vehicle Report for September 2025
        success3, towing_report = self.run_test("Towing Vehicle Report Sept 2025", "GET", "reports/revenue-by-towing-vehicle", 200, params={"month": 9, "year": 2025})
        
        towing_vehicles_found = []
        if success3 and towing_report:
            data = towing_report.get('data', [])
            for vehicle_data in data:
                vehicle_name = vehicle_data.get('towing_vehicle', '')
                if vehicle_name and vehicle_name != 'Unknown Vehicle':
                    towing_vehicles_found.append(vehicle_name)
            
            if len(towing_vehicles_found) >= 1:
                self.log_test("Imported Towing Vehicles in Report", True, f"Found towing vehicles: {', '.join(towing_vehicles_found[:3])}")
            else:
                self.log_test("Imported Towing Vehicles in Report", False, "No towing vehicles found in report")
        
        return success1 and success2 and success3
    
    def test_company_order_financials_imported(self):
        """Test company order financials with imported data"""
        print("\n💰 Testing Company Order Financials with Imported Data...")
        
        # Find a company order from imported data
        success1, company_orders = self.run_test("Get Company Orders for Financial Test", "GET", "orders", 200, params={"order_type": "company", "limit": 50})
        
        financial_test_passed = False
        if success1 and company_orders:
            for order in company_orders:
                if (order.get('company_name') == 'Europ Assistance' and 
                    order.get('company_service_type') == '2 Wheeler Towing'):
                    
                    order_id = order.get('id')
                    success2, financials = self.run_test(f"Get Financials for Imported Order", "GET", f"orders/{order_id}/financials", 200)
                    
                    if success2 and financials:
                        base_revenue = financials.get('base_revenue', 0)
                        total_revenue = financials.get('total_revenue', 0)
                        calculation_details = financials.get('calculation_details', '')
                        
                        if base_revenue > 0:
                            self.log_test("Imported Company Order Financials", True, f"Base: ₹{base_revenue}, Total: ₹{total_revenue}, Details: {calculation_details}")
                            financial_test_passed = True
                            break
                        else:
                            self.log_test("Imported Company Order Financials", False, f"Base revenue is 0, Details: {calculation_details}")
        
        if not financial_test_passed:
            self.log_test("Imported Company Order Financials", False, "Could not find suitable company order for financial testing")
        
        return financial_test_passed
    
    def test_no_pydantic_validation_errors(self):
        """Test that imported records don't cause Pydantic validation errors"""
        print("\n🔍 Testing No Pydantic Validation Errors...")
        
        # Test getting all orders without any validation errors
        success1, all_orders = self.run_test("Get All Orders - No Validation Errors", "GET", "orders", 200, params={"limit": 1000})
        
        if success1 and all_orders:
            # Check if we got a proper response without server errors
            if len(all_orders) >= 200:
                self.log_test("No Pydantic Validation Errors", True, f"Successfully retrieved {len(all_orders)} orders without validation errors")
                return True
            else:
                self.log_test("No Pydantic Validation Errors", False, f"Only retrieved {len(all_orders)} orders, expected more")
        else:
            self.log_test("No Pydantic Validation Errors", False, "Failed to retrieve orders - possible validation errors")
        
        return False

    def test_super_admin_password_reset_feature(self):
        """Test Super Admin Password Reset Feature comprehensively"""
        print("\n🔐 Testing Super Admin Password Reset Feature...")
        
        # Step 1: Login as Super Admin
        success1, login_response = self.run_test(
            "Super Admin Login for Password Reset",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@kawalecranes.com", "password": "admin123"}
        )
        
        if not success1 or 'access_token' not in login_response:
            return self.log_test("Super Admin Password Reset Feature", False, "Failed to login as Super Admin")
        
        # Store admin token
        admin_token = self.token
        super_admin_token = login_response['access_token']
        self.token = super_admin_token
        
        # Step 2: Create a test data_entry user for password reset testing
        test_user_data = {
            "email": "test_dataentry@test.com",
            "full_name": "Test Data Entry User",
            "password": "test123",
            "role": "data_entry"
        }
        
        success2, create_response = self.run_test(
            "Create Test Data Entry User",
            "POST",
            "auth/register",
            200,
            test_user_data
        )
        
        if not success2 or 'id' not in create_response:
            self.token = admin_token
            return self.log_test("Super Admin Password Reset Feature", False, "Failed to create test user")
        
        test_user_id = create_response['id']
        
        # Step 3: Test password reset with valid password (6+ chars)
        reset_data_valid = {"new_password": "newpass123"}
        success3, reset_response = self.run_test(
            "Password Reset - Valid Password",
            "PUT",
            f"users/{test_user_id}/reset-password",
            200,
            reset_data_valid
        )
        
        # Step 4: Test password reset with short password (<6 chars)
        reset_data_short = {"new_password": "123"}
        success4, _ = self.run_test(
            "Password Reset - Short Password (Should Fail)",
            "PUT",
            f"users/{test_user_id}/reset-password",
            400,
            reset_data_short
        )
        
        # Step 5: Test Super Admin trying to reset own password (should fail)
        super_admin_id = login_response['user']['id']
        reset_data_self = {"new_password": "newadminpass"}
        success5, _ = self.run_test(
            "Password Reset - Self Reset (Should Fail)",
            "PUT",
            f"users/{super_admin_id}/reset-password",
            400,
            reset_data_self
        )
        
        # Step 6: Verify audit log created for password reset
        success6, audit_response = self.run_test(
            "Check Audit Log for Password Reset",
            "GET",
            "audit-logs",
            200,
            params={"action": "UPDATE", "resource_type": "USER"}
        )
        
        audit_found = False
        if success6 and audit_response:
            for log in audit_response:
                if (log.get('resource_id') == test_user_id and 
                    log.get('action') == 'UPDATE' and 
                    log.get('new_data', {}).get('password') == '***'):
                    audit_found = True
                    break
        
        if audit_found:
            self.log_test("Password Reset Audit Log", True, "Audit log created for password reset")
        else:
            self.log_test("Password Reset Audit Log", False, "No audit log found for password reset")
        
        # Step 7: Test that user can login with new password
        self.token = None  # Remove admin token for login test
        success7, new_login_response = self.run_test(
            "Login with New Password",
            "POST",
            "auth/login",
            200,
            data={"email": "test_dataentry@test.com", "password": "newpass123"}
        )
        
        # Step 8: Test that old password no longer works
        success8, _ = self.run_test(
            "Login with Old Password (Should Fail)",
            "POST",
            "auth/login",
            401,
            data={"email": "test_dataentry@test.com", "password": "test123"}
        )
        
        # Cleanup: Delete test user
        self.token = super_admin_token
        self.run_test("Cleanup Test User", "DELETE", f"users/{test_user_id}", 200)
        
        # Restore original token
        self.token = admin_token
        
        # Overall success check
        all_tests_passed = all([success1, success2, success3, success4, success5, audit_found, success7, success8])
        
        if all_tests_passed:
            self.log_test("Super Admin Password Reset Feature", True, "All password reset tests passed")
        else:
            failed_tests = []
            if not success1: failed_tests.append("Super Admin Login")
            if not success2: failed_tests.append("Create Test User")
            if not success3: failed_tests.append("Valid Password Reset")
            if not success4: failed_tests.append("Short Password Validation")
            if not success5: failed_tests.append("Self Reset Prevention")
            if not audit_found: failed_tests.append("Audit Log Creation")
            if not success7: failed_tests.append("New Password Login")
            if not success8: failed_tests.append("Old Password Rejection")
            
            self.log_test("Super Admin Password Reset Feature", False, f"Failed tests: {', '.join(failed_tests)}")
        
        return all_tests_passed

    def test_data_entry_role_access_restrictions(self):
        """Test Data Entry Role Access Restrictions comprehensively"""
        print("\n🛡️ Testing Data Entry Role Access Restrictions...")
        
        # Step 1: Login as Super Admin to create data entry user
        success1, admin_login_response = self.run_test(
            "Admin Login for Role Testing",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@kawalecranes.com", "password": "admin123"}
        )
        
        if not success1 or 'access_token' not in admin_login_response:
            return self.log_test("Data Entry Role Access Restrictions", False, "Failed to login as Admin")
        
        admin_token = admin_login_response['access_token']
        self.token = admin_token
        
        # Step 2: Create data entry user
        data_entry_user = {
            "email": "dataentry_test@kawalecranes.com",
            "full_name": "Data Entry Test User",
            "password": "dataentry123",
            "role": "data_entry"
        }
        
        success2, create_response = self.run_test(
            "Create Data Entry User",
            "POST",
            "auth/register",
            200,
            data_entry_user
        )
        
        if not success2 or 'id' not in create_response:
            return self.log_test("Data Entry Role Access Restrictions", False, "Failed to create data entry user")
        
        data_entry_user_id = create_response['id']
        
        # Step 3: Login as data entry user
        success3, de_login_response = self.run_test(
            "Data Entry User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "dataentry_test@kawalecranes.com", "password": "dataentry123"}
        )
        
        if not success3 or 'access_token' not in de_login_response:
            self.token = admin_token
            self.run_test("Cleanup Data Entry User", "DELETE", f"users/{data_entry_user_id}", 200)
            return self.log_test("Data Entry Role Access Restrictions", False, "Failed to login as data entry user")
        
        data_entry_token = de_login_response['access_token']
        self.token = data_entry_token
        
        # Step 4: Test what Data Entry user CAN access
        print("   Testing Data Entry user ALLOWED access...")
        
        # Can view rates
        success4a, _ = self.run_test("Data Entry - View Rates (Should Work)", "GET", "rates", 200)
        
        # Can create orders
        test_order = {
            "customer_name": "Data Entry Test Order",
            "phone": "9876543999",
            "order_type": "cash",
            "cash_vehicle_name": "Test Vehicle",
            "amount_received": 1000.0
        }
        success4b, order_response = self.run_test("Data Entry - Create Order (Should Work)", "POST", "orders", 200, test_order)
        
        created_order_id = None
        if success4b and 'id' in order_response:
            created_order_id = order_response['id']
        
        # Can view orders
        success4c, _ = self.run_test("Data Entry - View Orders (Should Work)", "GET", "orders", 200)
        
        # Can edit orders
        success4d = True
        if created_order_id:
            update_data = {"customer_name": "Updated by Data Entry"}
            success4d, _ = self.run_test("Data Entry - Edit Order (Should Work)", "PUT", f"orders/{created_order_id}", 200, update_data)
        
        # Step 5: Test what Data Entry user CANNOT access
        print("   Testing Data Entry user FORBIDDEN access...")
        
        # Cannot access audit logs
        success5a, _ = self.run_test("Data Entry - Audit Logs (Should Fail)", "GET", "audit-logs", 403)
        
        # Cannot access expense reports
        success5b, _ = self.run_test("Data Entry - Expense Report (Should Fail)", "GET", "reports/expense-by-driver", 403, params={"month": 10, "year": 2024})
        
        # Cannot access revenue reports
        success5c, _ = self.run_test("Data Entry - Revenue Report (Should Fail)", "GET", "reports/revenue-by-vehicle-type", 403, params={"month": 10, "year": 2024})
        
        # Cannot access import excel
        success5d, _ = self.run_test("Data Entry - Import Excel (Should Fail)", "POST", "import/excel", 403)
        
        # Cannot edit rates
        if success4a:  # If we got rates successfully, try to edit one
            # Get a rate ID first
            rates_response = self.run_test("Get Rates for Edit Test", "GET", "rates", 200)[1]
            if rates_response and len(rates_response) > 0:
                rate_id = rates_response[0]['id']
                update_rate_data = {"base_rate": 1500}
                success5e, _ = self.run_test("Data Entry - Edit Rate (Should Fail)", "PUT", f"rates/{rate_id}", 403, update_rate_data)
            else:
                success5e = True  # No rates to test with, consider it passed
        else:
            success5e = True
        
        # Cannot create rates
        new_rate_data = {
            "name_of_firm": "Test Firm",
            "company_name": "Test Company",
            "service_type": "Test Service",
            "base_rate": 1000,
            "rate_per_km_beyond": 10
        }
        success5f, _ = self.run_test("Data Entry - Create Rate (Should Fail)", "POST", "rates", 403, new_rate_data)
        
        # Cannot delete rates
        if success4a:  # If we got rates successfully, try to delete one
            rates_response = self.run_test("Get Rates for Delete Test", "GET", "rates", 200)[1]
            if rates_response and len(rates_response) > 0:
                rate_id = rates_response[0]['id']
                success5g, _ = self.run_test("Data Entry - Delete Rate (Should Fail)", "DELETE", f"rates/{rate_id}", 403)
            else:
                success5g = True  # No rates to test with, consider it passed
        else:
            success5g = True
        
        # Cannot access user management
        success5h, _ = self.run_test("Data Entry - User Management (Should Fail)", "GET", "users", 403)
        
        # Step 6: Test Admin/Super Admin access still works
        print("   Testing Admin access still works...")
        self.token = admin_token
        
        # Admin can access reports
        success6a, _ = self.run_test("Admin - Expense Report (Should Work)", "GET", "reports/expense-by-driver", 200, params={"month": 10, "year": 2024})
        
        # Admin can edit rates
        if success4a:
            rates_response = self.run_test("Get Rates for Admin Edit Test", "GET", "rates", 200)[1]
            if rates_response and len(rates_response) > 0:
                rate_id = rates_response[0]['id']
                update_rate_data = {"base_rate": 1600}
                success6b, _ = self.run_test("Admin - Edit Rate (Should Work)", "PUT", f"rates/{rate_id}", 200, update_rate_data)
            else:
                success6b = True
        else:
            success6b = True
        
        # Admin can access user management
        success6c, _ = self.run_test("Admin - User Management (Should Work)", "GET", "users", 200)
        
        # Cleanup: Delete test order and user
        if created_order_id:
            self.run_test("Cleanup Test Order", "DELETE", f"orders/{created_order_id}", 200)
        
        self.run_test("Cleanup Data Entry User", "DELETE", f"users/{data_entry_user_id}", 200)
        
        # Overall success check
        allowed_access_tests = [success4a, success4b, success4c, success4d]
        forbidden_access_tests = [success5a, success5b, success5c, success5d, success5e, success5f, success5g, success5h]
        admin_access_tests = [success6a, success6b, success6c]
        
        all_allowed_passed = all(allowed_access_tests)
        all_forbidden_passed = all(forbidden_access_tests)
        all_admin_passed = all(admin_access_tests)
        
        overall_success = all_allowed_passed and all_forbidden_passed and all_admin_passed
        
        if overall_success:
            self.log_test("Data Entry Role Access Restrictions", True, "All role access restriction tests passed")
        else:
            failed_categories = []
            if not all_allowed_passed: failed_categories.append("Data Entry Allowed Access")
            if not all_forbidden_passed: failed_categories.append("Data Entry Forbidden Access")
            if not all_admin_passed: failed_categories.append("Admin Access Verification")
            
            self.log_test("Data Entry Role Access Restrictions", False, f"Failed categories: {', '.join(failed_categories)}")
        
        return overall_success

    def test_change_password_functionality(self):
        """Comprehensive test of Change Password functionality"""
        print("\n🔐 Testing Change Password Functionality...")
        
        # Step 1: Login as Admin to get token
        success1, login_response = self.run_test(
            "Admin Login for Password Change",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@kawalecranes.com", "password": "admin123"}
        )
        
        if not success1 or 'access_token' not in login_response:
            self.log_test("Change Password Setup", False, "Failed to login as admin")
            return False
        
        # Store the token for authenticated requests
        old_token = self.token
        self.token = login_response['access_token']
        
        # Step 2: Test Valid Password Change (admin123 -> newpass123)
        change_password_data = {
            "current_password": "admin123",
            "new_password": "newpass123"
        }
        
        success2, response2 = self.run_test(
            "Valid Password Change",
            "PUT",
            "auth/change-password",
            200,
            data=change_password_data
        )
        
        if success2 and response2:
            message = response2.get('message', '')
            if 'successfully' in message.lower():
                self.log_test("Password Change Success Message", True, f"Message: {message}")
            else:
                self.log_test("Password Change Success Message", False, f"Unexpected message: {message}")
        
        # Step 3: Test Login with New Password (newpass123)
        success3, new_login_response = self.run_test(
            "Login with New Password",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@kawalecranes.com", "password": "newpass123"}
        )
        
        if success3 and 'access_token' in new_login_response:
            self.log_test("New Password Login Token", True, "Successfully obtained token with new password")
            # Update token for subsequent requests
            self.token = new_login_response['access_token']
        
        # Step 4: Test Login with Old Password (Should Fail)
        success4, old_login_response = self.run_test(
            "Login with Old Password (Should Fail)",
            "POST",
            "auth/login",
            401,
            data={"email": "admin@kawalecranes.com", "password": "admin123"}
        )
        
        if success4 and old_login_response:
            detail = old_login_response.get('detail', '')
            if 'incorrect' in detail.lower() or 'password' in detail.lower():
                self.log_test("Old Password Rejection Message", True, f"Correct rejection: {detail}")
            else:
                self.log_test("Old Password Rejection Message", False, f"Unexpected error: {detail}")
        
        # Step 5: Change Password Back to Original (newpass123 -> admin123)
        restore_password_data = {
            "current_password": "newpass123",
            "new_password": "admin123"
        }
        
        success5, response5 = self.run_test(
            "Restore Original Password",
            "PUT",
            "auth/change-password",
            200,
            data=restore_password_data
        )
        
        # Step 6: Verify Original Password Works Again
        success6, restore_login_response = self.run_test(
            "Login with Restored Password",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@kawalecranes.com", "password": "admin123"}
        )
        
        if success6 and 'access_token' in restore_login_response:
            self.token = restore_login_response['access_token']
        
        # Step 7: Test Error Cases
        
        # Test wrong current password
        success7, response7 = self.run_test(
            "Wrong Current Password",
            "PUT",
            "auth/change-password",
            400,
            data={"current_password": "wrongpassword", "new_password": "newpass123"}
        )
        
        if success7 and response7:
            detail = response7.get('detail', '')
            if 'incorrect' in detail.lower() or 'current password' in detail.lower():
                self.log_test("Wrong Current Password Error", True, f"Correct error: {detail}")
            else:
                self.log_test("Wrong Current Password Error", False, f"Unexpected error: {detail}")
        
        # Test short password (less than 6 characters)
        success8, response8 = self.run_test(
            "Short Password Validation",
            "PUT",
            "auth/change-password",
            400,
            data={"current_password": "admin123", "new_password": "12345"}
        )
        
        if success8 and response8:
            detail = response8.get('detail', '')
            if '6 characters' in detail or 'least 6' in detail:
                self.log_test("Short Password Error Message", True, f"Correct validation: {detail}")
            else:
                self.log_test("Short Password Error Message", False, f"Unexpected error: {detail}")
        
        # Test same password as current
        success9, response9 = self.run_test(
            "Same Password Validation",
            "PUT",
            "auth/change-password",
            400,
            data={"current_password": "admin123", "new_password": "admin123"}
        )
        
        if success9 and response9:
            detail = response9.get('detail', '')
            if 'different' in detail.lower() or 'same' in detail.lower():
                self.log_test("Same Password Error Message", True, f"Correct validation: {detail}")
            else:
                self.log_test("Same Password Error Message", False, f"Unexpected error: {detail}")
        
        # Test missing current password
        success10, response10 = self.run_test(
            "Missing Current Password",
            "PUT",
            "auth/change-password",
            400,
            data={"new_password": "newpass123"}
        )
        
        if success10 and response10:
            detail = response10.get('detail', '')
            if 'required' in detail.lower() or 'current password' in detail.lower():
                self.log_test("Missing Current Password Error", True, f"Correct validation: {detail}")
            else:
                self.log_test("Missing Current Password Error", False, f"Unexpected error: {detail}")
        
        # Test missing new password
        success11, response11 = self.run_test(
            "Missing New Password",
            "PUT",
            "auth/change-password",
            400,
            data={"current_password": "admin123"}
        )
        
        if success11 and response11:
            detail = response11.get('detail', '')
            if 'required' in detail.lower() or 'new password' in detail.lower():
                self.log_test("Missing New Password Error", True, f"Correct validation: {detail}")
            else:
                self.log_test("Missing New Password Error", False, f"Unexpected error: {detail}")
        
        # Test audit log creation for password change
        success12, audit_response = self.run_test(
            "Check Audit Log for Password Change",
            "GET",
            "audit-logs",
            200,
            params={"action": "UPDATE", "resource_type": "USER", "limit": 10}
        )
        
        audit_found = False
        if success12 and audit_response:
            logs = audit_response if isinstance(audit_response, list) else []
            for log in logs:
                if (log.get('action') == 'UPDATE' and 
                    log.get('resource_type') == 'USER' and
                    log.get('user_email') == 'admin@kawalecranes.com' and
                    log.get('new_data', {}).get('password') == '***'):
                    audit_found = True
                    break
            
            if audit_found:
                self.log_test("Password Change Audit Log", True, "Password change properly logged in audit trail")
            else:
                self.log_test("Password Change Audit Log", False, "Password change audit log not found or incorrect format")
        
        # Restore original token
        self.token = old_token
        
        # Calculate overall success
        all_tests = [success1, success2, success3, success4, success5, success6, 
                    success7, success8, success9, success10, success11, audit_found]
        
        overall_success = all(all_tests)
        
        if overall_success:
            self.log_test("Change Password Overall", True, "All change password functionality tests passed")
        else:
            failed_count = len([s for s in all_tests if not s])
            self.log_test("Change Password Overall", False, f"{failed_count} out of {len(all_tests)} tests failed")
        
        return overall_success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Kawale Cranes Backend API Tests")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 80)

        # First login to get authentication token
        if not self.test_login():
            print("❌ Login failed, stopping tests")
            return 1

        # Run Excel Import Verification first - PRIMARY FOCUS
        print("\n🎯 EXCEL IMPORT VERIFICATION - PRIMARY FOCUS")
        print("=" * 80)
        self.test_excel_import_verification()
        self.test_reports_with_imported_data()
        self.test_company_order_financials_imported()
        self.test_no_pydantic_validation_errors()
        
        # Run review request priorities
        print("\n🎯 REVIEW REQUEST TESTING")
        print("=" * 80)
        self.test_review_request_priorities()
        
        # NEW FEATURES TESTING - PRIMARY FOCUS
        print("\n🎯 NEW FEATURES TESTING - PRIMARY FOCUS")
        print("=" * 80)
        self.test_super_admin_password_reset_feature()
        self.test_data_entry_role_access_restrictions()
        
        # CHANGE PASSWORD FUNCTIONALITY TESTING - REVIEW REQUEST
        print("\n🎯 CHANGE PASSWORD FUNCTIONALITY TESTING - REVIEW REQUEST")
        print("=" * 80)
        self.test_change_password_functionality()

        # Test sequence - organized by functionality
        test_methods = [
            # Core API Tests
            self.test_root_endpoint,
            
            # Authentication System Tests
            self.test_authentication_system,
            
            # PRIMARY FOCUS: Mandatory Fields Validation Testing
            self.test_mandatory_fields_validation_comprehensive,
            self.test_mandatory_fields_update_validation,
            self.test_cash_orders_no_validation,
            self.test_incentive_functionality_regression,
            self.test_revenue_calculations_regression,
            
            # SK Rates Calculation System Tests
            self.test_sk_rates_calculation_system,
            
            # Order Management CRUD Tests
            self.test_create_cash_order,
            self.test_create_company_order,
            self.test_get_all_orders,
            self.test_get_single_order,
            self.test_update_order,
            self.test_delete_order,
            
            # Advanced Order Features Tests
            self.test_cash_order_with_driver_dropdown,
            self.test_company_order_with_dropdowns,
            self.test_care_off_fields_cash_order,
            self.test_care_off_fields_optional,
            self.test_care_off_fields_company_order,
            self.test_care_off_amount_validation,
            self.test_incentive_fields_admin_only,
            self.test_incentive_fields_optional,
            self.test_reach_drop_time_company_orders,
            self.test_all_driver_options,
            self.test_all_firm_options,
            self.test_all_company_options,
            
            # Filtering and Search Tests
            self.test_filtering_functionality,
            self.test_get_orders_with_filters,
            
            # User Management Tests (Super Admin functionality)
            self.test_user_management_endpoints,
            
            # Role-Based Access Control Tests
            self.test_role_based_access_control,
            
            # Export Endpoints Tests
            self.test_export_endpoints,
            
            # Monthly Reports System Tests
            self.test_monthly_reports_system,
            
            # NEW REPORTING & RATES FEATURES (Review Request Priority)
            self.test_new_reporting_features,
            self.test_create_new_rates,
            self.test_excel_import_investigation,
            
            # Audit Logging Tests
            self.test_audit_logging,
            
            # MongoDB Connection Tests
            self.test_mongodb_connections,
            
            # Advanced Order Operations
            self.test_update_order_with_care_off,
            self.test_update_order_with_incentive,
            self.test_mixed_order_types_with_features,
            self.test_bulk_delete_multiple_orders,
            
            # Statistics and Summary Tests
            self.test_get_stats_summary,
            
            # Error Handling Tests
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
        print("=" * 80)
        print(f"📊 COMPREHENSIVE TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Categorize results
        failed_tests = [result for result in self.test_results if not result['success']]
        critical_failures = []
        minor_failures = []
        
        for result in failed_tests:
            if any(keyword in result['test_name'].lower() for keyword in ['login', 'auth', 'create', 'delete', 'export']):
                critical_failures.append(result)
            else:
                minor_failures.append(result)
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            
            if critical_failures:
                print(f"\n🚨 CRITICAL FAILURES ({len(critical_failures)}):")
                for result in critical_failures:
                    print(f"  - {result['test_name']}: {result['details']}")
            
            if minor_failures:
                print(f"\n⚠️ MINOR FAILURES ({len(minor_failures)}):")
                for result in minor_failures:
                    print(f"  - {result['test_name']}: {result['details']}")
            
            return 1

    def run_google_sheets_removal_tests(self):
        """Run tests specifically for Google Sheets removal verification"""
        print("🗑️ Starting Google Sheets Removal Verification Tests...")
        print(f"🌐 Testing against: {self.api_url}")
        print("=" * 80)
        
        # Login first
        if not self.test_login():
            print("❌ Login failed - cannot continue with authenticated tests")
            return False
        
        # Run specific tests for the review request
        test_methods = [
            # Authentication Test
            self.test_authentication_system,
            
            # Orders API Test
            self.test_get_all_orders,
            self.test_create_cash_order,
            self.test_create_company_order,
            
            # Export Endpoints Test
            self.test_export_endpoints,
            
            # Google Sheets Removal Verification
            self.test_google_sheets_removal_verification,
            
            # Basic CRUD Test
            self.test_get_single_order,
            self.test_update_order
        ]
        
        print("\n📋 Running Google Sheets Removal Tests")
        print("-" * 60)
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Test execution error: {str(e)}")
        
        # Cleanup created orders
        self.cleanup_created_orders()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 GOOGLE SHEETS REMOVAL TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        overall_success = self.tests_passed == self.tests_run
        
        if overall_success:
            print("🎉 ALL GOOGLE SHEETS REMOVAL TESTS PASSED!")
            print("✅ Authentication working with admin@kawalecranes.com / admin123")
            print("✅ Orders API (GET /api/orders) working correctly")
            print("✅ Excel export working correctly")
            print("✅ PDF export working correctly")
            print("✅ Google Sheets endpoint properly removed (404 Not Found)")
            print("✅ Basic CRUD operations working correctly")
        else:
            print("⚠️  SOME TESTS FAILED - Check details above")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ FAILED TESTS:")
                for result in failed_tests:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        return overall_success

def main():
    """Main test execution"""
    tester = CraneOrderAPITester()
    
    # Check if we should run focused dashboard test
    if len(sys.argv) > 1 and sys.argv[1] == "--dashboard":
        return 0 if tester.run_focused_dashboard_test() else 1
    elif len(sys.argv) > 1 and sys.argv[1] == "--google-sheets-removal":
        return 0 if tester.run_google_sheets_removal_tests() else 1
    else:
        return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())