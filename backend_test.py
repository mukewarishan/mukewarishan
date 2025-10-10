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

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Kawale Cranes Backend API Tests")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 80)

        # First login to get authentication token
        if not self.test_login():
            print("❌ Login failed, stopping tests")
            return 1

        # Run review request priorities first
        print("\n🎯 REVIEW REQUEST TESTING")
        print("=" * 80)
        self.test_review_request_priorities()

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
    
    # Check if we should run focused dashboard test
    if len(sys.argv) > 1 and sys.argv[1] == "--dashboard":
        return 0 if tester.run_focused_dashboard_test() else 1
    else:
        return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())