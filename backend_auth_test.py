#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import uuid

class AuthenticationAPITester:
    def __init__(self, base_url="https://kawale-fleet-hub.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.tokens = {}  # Store tokens for different users
        self.created_users = []
        self.created_orders = []

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

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
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

    def test_login_super_admin(self):
        """Test login with default super admin credentials"""
        login_data = {
            "email": "admin@kawalecranes.com",
            "password": "admin123"
        }
        
        success, response = self.run_test("Login Super Admin", "POST", "auth/login", 200, login_data)
        if success and response:
            self.tokens['super_admin'] = response.get('access_token')
            user_data = response.get('user', {})
            if user_data.get('role') == 'super_admin':
                return self.log_test("Verify Super Admin Role", True, f"Role: {user_data.get('role')}")
            else:
                return self.log_test("Verify Super Admin Role", False, f"Expected super_admin, got {user_data.get('role')}")
        return success

    def test_login_data_entry_user(self):
        """Test login with data entry user credentials"""
        login_data = {
            "email": "operator@kawalecranes.com",
            "password": "operator123"
        }
        
        success, response = self.run_test("Login Data Entry User", "POST", "auth/login", 200, login_data)
        if success and response:
            self.tokens['data_entry'] = response.get('access_token')
            user_data = response.get('user', {})
            if user_data.get('role') == 'data_entry':
                return self.log_test("Verify Data Entry Role", True, f"Role: {user_data.get('role')}")
            else:
                return self.log_test("Verify Data Entry Role", False, f"Expected data_entry, got {user_data.get('role')}")
        return success

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        invalid_login_data = {
            "email": "invalid@kawalecranes.com",
            "password": "wrongpassword"
        }
        
        return self.run_test("Invalid Login", "POST", "auth/login", 401, invalid_login_data)

    def test_get_current_user(self):
        """Test getting current user info"""
        if 'super_admin' not in self.tokens:
            return self.log_test("Get Current User", False, "No super admin token available")
        
        return self.run_test("Get Current User", "GET", "auth/me", 200, token=self.tokens['super_admin'])

    def test_create_new_user(self):
        """Test creating a new user (Admin functionality)"""
        if 'super_admin' not in self.tokens:
            return self.log_test("Create New User", False, "No super admin token available")
        
        new_user_data = {
            "email": f"testuser_{datetime.now().strftime('%H%M%S')}@kawalecranes.com",
            "full_name": "Test User",
            "password": "testpass123",
            "role": "data_entry"
        }
        
        success, response = self.run_test("Create New User", "POST", "auth/register", 200, new_user_data, token=self.tokens['super_admin'])
        if success and response:
            self.created_users.append(response.get('id'))
        return success

    def test_create_user_without_permission(self):
        """Test creating user without admin permissions"""
        if 'data_entry' not in self.tokens:
            return self.log_test("Create User Without Permission", False, "No data entry token available")
        
        new_user_data = {
            "email": f"unauthorized_{datetime.now().strftime('%H%M%S')}@kawalecranes.com",
            "full_name": "Unauthorized User",
            "password": "testpass123",
            "role": "data_entry"
        }
        
        return self.run_test("Create User Without Permission", "POST", "auth/register", 403, new_user_data, token=self.tokens['data_entry'])

    def test_get_users_list(self):
        """Test getting users list (Admin functionality)"""
        if 'super_admin' not in self.tokens:
            return self.log_test("Get Users List", False, "No super admin token available")
        
        return self.run_test("Get Users List", "GET", "users", 200, token=self.tokens['super_admin'])

    def test_get_users_without_permission(self):
        """Test getting users list without admin permissions"""
        if 'data_entry' not in self.tokens:
            return self.log_test("Get Users Without Permission", False, "No data entry token available")
        
        return self.run_test("Get Users Without Permission", "GET", "users", 403, token=self.tokens['data_entry'])

    def test_create_order_with_auth(self):
        """Test creating order with authentication"""
        if 'data_entry' not in self.tokens:
            return self.log_test("Create Order With Auth", False, "No data entry token available")
        
        order_data = {
            "customer_name": "Auth Test Customer",
            "phone": "9876543210",
            "order_type": "cash",
            "cash_trip_from": "Mumbai",
            "cash_trip_to": "Pune",
            "amount_received": 5000.0
        }
        
        success, response = self.run_test("Create Order With Auth", "POST", "orders", 200, order_data, token=self.tokens['data_entry'])
        if success and response:
            self.created_orders.append(response.get('id'))
        return success

    def test_create_order_without_auth(self):
        """Test creating order without authentication"""
        order_data = {
            "customer_name": "Unauthorized Customer",
            "phone": "9876543210",
            "order_type": "cash"
        }
        
        return self.run_test("Create Order Without Auth", "POST", "orders", 401, order_data)

    def test_delete_order_with_admin_role(self):
        """Test deleting order with admin role"""
        if 'super_admin' not in self.tokens or not self.created_orders:
            return self.log_test("Delete Order With Admin", False, "No super admin token or orders available")
        
        order_id = self.created_orders[0]
        success, _ = self.run_test("Delete Order With Admin", "DELETE", f"orders/{order_id}", 200, token=self.tokens['super_admin'])
        if success:
            self.created_orders.remove(order_id)
        return success

    def test_delete_order_without_permission(self):
        """Test deleting order without admin permissions"""
        if 'data_entry' not in self.tokens or not self.created_orders:
            return self.log_test("Delete Order Without Permission", False, "No data entry token or orders available")
        
        order_id = self.created_orders[0] if self.created_orders else "dummy-id"
        return self.run_test("Delete Order Without Permission", "DELETE", f"orders/{order_id}", 403, token=self.tokens['data_entry'])

    def test_get_audit_logs(self):
        """Test getting audit logs (Admin functionality)"""
        if 'super_admin' not in self.tokens:
            return self.log_test("Get Audit Logs", False, "No super admin token available")
        
        return self.run_test("Get Audit Logs", "GET", "audit-logs", 200, token=self.tokens['super_admin'])

    def test_get_audit_logs_without_permission(self):
        """Test getting audit logs without admin permissions"""
        if 'data_entry' not in self.tokens:
            return self.log_test("Get Audit Logs Without Permission", False, "No data entry token available")
        
        return self.run_test("Get Audit Logs Without Permission", "GET", "audit-logs", 403, token=self.tokens['data_entry'])

    def test_audit_logs_filtering(self):
        """Test audit logs with filters"""
        if 'super_admin' not in self.tokens:
            return self.log_test("Audit Logs Filtering", False, "No super admin token available")
        
        # Test filter by resource type
        success1, _ = self.run_test("Filter Audit Logs by USER", "GET", "audit-logs", 200, params={"resource_type": "USER"}, token=self.tokens['super_admin'])
        success2, _ = self.run_test("Filter Audit Logs by ORDER", "GET", "audit-logs", 200, params={"resource_type": "ORDER"}, token=self.tokens['super_admin'])
        success3, _ = self.run_test("Filter Audit Logs by LOGIN", "GET", "audit-logs", 200, params={"action": "LOGIN"}, token=self.tokens['super_admin'])
        
        return success1 and success2 and success3

    def test_logout(self):
        """Test logout functionality"""
        if 'super_admin' not in self.tokens:
            return self.log_test("Logout", False, "No super admin token available")
        
        return self.run_test("Logout", "POST", "auth/logout", 200, token=self.tokens['super_admin'])

    def test_expired_token_handling(self):
        """Test handling of invalid/expired tokens"""
        fake_token = "invalid.jwt.token"
        return self.run_test("Invalid Token Handling", "GET", "auth/me", 401, token=fake_token)

    def cleanup_created_resources(self):
        """Clean up any remaining test resources"""
        print("\n🧹 Cleaning up test resources...")
        
        # Clean up orders
        for order_id in self.created_orders[:]:
            try:
                if 'super_admin' in self.tokens:
                    headers = {'Authorization': f'Bearer {self.tokens["super_admin"]}'}
                    response = requests.delete(f"{self.api_url}/orders/{order_id}", headers=headers, timeout=5)
                    if response.status_code == 200:
                        print(f"✅ Cleaned up order: {order_id}")
                        self.created_orders.remove(order_id)
                    else:
                        print(f"⚠️ Failed to cleanup order: {order_id}")
            except Exception as e:
                print(f"⚠️ Error cleaning up order {order_id}: {str(e)}")

    def run_all_tests(self):
        """Run all authentication API tests"""
        print("🚀 Starting Authentication & Authorization API Tests")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 70)

        # Test sequence
        test_methods = [
            # Authentication tests
            self.test_login_super_admin,
            self.test_login_data_entry_user,
            self.test_invalid_login,
            self.test_get_current_user,
            
            # User management tests
            self.test_create_new_user,
            self.test_create_user_without_permission,
            self.test_get_users_list,
            self.test_get_users_without_permission,
            
            # Order operations with auth
            self.test_create_order_with_auth,
            self.test_create_order_without_auth,
            self.test_delete_order_with_admin_role,
            self.test_delete_order_without_permission,
            
            # Audit logs tests
            self.test_get_audit_logs,
            self.test_get_audit_logs_without_permission,
            self.test_audit_logs_filtering,
            
            # Session management
            self.test_logout,
            self.test_expired_token_handling
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Test execution error: {str(e)}")
            print()

        # Cleanup
        self.cleanup_created_resources()

        # Print summary
        print("=" * 70)
        print(f"📊 AUTHENTICATION TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All authentication tests passed!")
            return 0
        else:
            print("❌ Some authentication tests failed!")
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['details']}")
            return 1

def main():
    """Main test execution"""
    tester = AuthenticationAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())