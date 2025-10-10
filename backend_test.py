#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import uuid

class CraneOrderAPITester:
    def __init__(self, base_url="https://kawale-data.preview.emergentagent.com"):
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
        
        # Test Google Sheets export (should fail without proper config)
        success3, sheets_response = self.run_test("Google Sheets Export", "GET", "export/googlesheets", 500)
        
        # Test export with filters
        success4, _ = self.run_test("PDF Export with Filters", "GET", "export/pdf", 200, params={"order_type": "cash", "limit": 10})
        success5, _ = self.run_test("Excel Export with Filters", "GET", "export/excel", 200, params={"order_type": "company", "limit": 10})
        
        return success1 and success2 and success3 and success4 and success5

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
        print("🚀 Starting Kawale Cranes Backend API Tests")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 80)

        # First login to get authentication token
        if not self.test_login():
            print("❌ Login failed, stopping tests")
            return 1

        # Test sequence - organized by functionality
        test_methods = [
            # Core API Tests
            self.test_root_endpoint,
            
            # Authentication System Tests
            self.test_authentication_system,
            
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

def main():
    """Main test execution"""
    tester = CraneOrderAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())