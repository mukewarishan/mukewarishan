#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timezone
import uuid

class UserManagementAPITester:
    def __init__(self, base_url="https://kawale-data.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_users = []
        self.token = None
        self.current_user_id = None

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

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, response_type='json'):
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
                if response_type == 'json':
                    try:
                        response_json = response.json()
                        details = f"Status: {response.status_code}"
                        return self.log_test(name, True, details, response_json), response_json
                    except:
                        details = f"Status: {response.status_code} (No JSON response)"
                        return self.log_test(name, True, details), {}
                elif response_type == 'binary':
                    details = f"Status: {response.status_code}, Content-Length: {len(response.content)}"
                    return self.log_test(name, True, details), response.content
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

    def test_super_admin_login(self):
        """Test Super Admin login and get token"""
        success, response = self.run_test(
            "Super Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@kawalecranes.com", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.current_user_id = response['user']['id']
            self.log_test("Token Obtained", True, f"Token length: {len(self.token)}")
            return True
        return False

    def test_get_users_list(self):
        """Test getting users list (Super Admin/Admin only)"""
        success, response = self.run_test(
            "Get Users List",
            "GET",
            "users",
            200
        )
        if success and isinstance(response, list):
            self.log_test("Users List Retrieved", True, f"Found {len(response)} users")
            return True, response
        return False, []

    def test_create_user(self):
        """Test creating a new user (Super Admin/Admin only)"""
        test_user_data = {
            "email": f"test_user_{datetime.now().strftime('%H%M%S')}@kawalecranes.com",
            "full_name": "Test User for Management",
            "password": "testpass123",
            "role": "data_entry"
        }
        
        success, response = self.run_test(
            "Create New User",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success and 'id' in response:
            self.created_users.append(response['id'])
            self.log_test("User Creation Verified", True, f"Created user: {response['email']}")
            return True, response
        return False, {}

    def test_update_user(self):
        """Test updating user details (Super Admin/Admin only)"""
        if not self.created_users:
            return self.log_test("Update User", False, "No users created to test with")
        
        user_id = self.created_users[0]
        update_data = {
            "full_name": "Updated Test User Name",
            "role": "admin",
            "is_active": True
        }
        
        success, response = self.run_test(
            "Update User Details",
            "PUT",
            f"users/{user_id}",
            200,
            data=update_data
        )
        
        if success and response:
            # Verify the update worked
            name_updated = response.get('full_name') == "Updated Test User Name"
            role_updated = response.get('role') == "admin"
            
            if name_updated and role_updated:
                self.log_test("User Update Verification", True, "User details updated successfully")
                return True
            else:
                self.log_test("User Update Verification", False, f"Name: {response.get('full_name')}, Role: {response.get('role')}")
        return False

    def test_delete_user_self_prevention(self):
        """Test that Super Admin cannot delete their own account"""
        success, response = self.run_test(
            "Prevent Self-Deletion",
            "DELETE",
            f"users/{self.current_user_id}",
            400  # Should return 400 Bad Request
        )
        return success

    def test_delete_user(self):
        """Test deleting a user (Super Admin only)"""
        if not self.created_users:
            return self.log_test("Delete User", False, "No users created to test with")
        
        user_id = self.created_users[-1]  # Delete the last created user
        success, response = self.run_test(
            "Delete User",
            "DELETE",
            f"users/{user_id}",
            200
        )
        
        if success:
            self.created_users.remove(user_id)
            self.log_test("User Deletion Verified", True, "User deleted successfully")
        return success

    def test_export_excel(self):
        """Test Excel export functionality (Admin/Super Admin only)"""
        success, response = self.run_test(
            "Export Orders to Excel",
            "GET",
            "export/excel",
            200,
            response_type='binary'
        )
        
        if success and isinstance(response, bytes) and len(response) > 0:
            self.log_test("Excel Export Verification", True, f"Excel file size: {len(response)} bytes")
            return True
        return False

    def test_export_pdf(self):
        """Test PDF export functionality (Admin/Super Admin only)"""
        success, response = self.run_test(
            "Export Orders to PDF",
            "GET",
            "export/pdf",
            200,
            response_type='binary'
        )
        
        if success and isinstance(response, bytes) and len(response) > 0:
            self.log_test("PDF Export Verification", True, f"PDF file size: {len(response)} bytes")
            return True
        return False

    def test_export_with_filters(self):
        """Test export functionality with filters"""
        # Test Excel export with filters
        success1, response1 = self.run_test(
            "Export Excel with Filters",
            "GET",
            "export/excel",
            200,
            params={"order_type": "cash", "limit": 100},
            response_type='binary'
        )
        
        # Test PDF export with filters
        success2, response2 = self.run_test(
            "Export PDF with Filters",
            "GET",
            "export/pdf",
            200,
            params={"order_type": "company", "limit": 50},
            response_type='binary'
        )
        
        return success1 and success2

    def test_audit_logs_access(self):
        """Test audit logs access (Admin/Super Admin only)"""
        success, response = self.run_test(
            "Access Audit Logs",
            "GET",
            "audit-logs",
            200,
            params={"limit": 10}
        )
        
        if success and isinstance(response, list):
            self.log_test("Audit Logs Retrieved", True, f"Found {len(response)} audit log entries")
            return True
        return False

    def test_role_based_access_control(self):
        """Test role-based access control by creating a data_entry user and testing restrictions"""
        # First create a data_entry user
        data_entry_user = {
            "email": f"dataentry_{datetime.now().strftime('%H%M%S')}@kawalecranes.com",
            "full_name": "Data Entry Test User",
            "password": "datapass123",
            "role": "data_entry"
        }
        
        success, user_response = self.run_test(
            "Create Data Entry User",
            "POST",
            "auth/register",
            200,
            data=data_entry_user
        )
        
        if not success:
            return False
        
        self.created_users.append(user_response['id'])
        
        # Login as data_entry user
        login_success, login_response = self.run_test(
            "Data Entry User Login",
            "POST",
            "auth/login",
            200,
            data={"email": data_entry_user["email"], "password": data_entry_user["password"]}
        )
        
        if not login_success:
            return False
        
        # Store original token
        original_token = self.token
        self.token = login_response['access_token']
        
        # Test that data_entry user cannot access user management
        success1, _ = self.run_test(
            "Data Entry User - Users Access Denied",
            "GET",
            "users",
            403  # Should be forbidden
        )
        
        # Test that data_entry user cannot access export functions
        success2, _ = self.run_test(
            "Data Entry User - Export Access Denied",
            "GET",
            "export/excel",
            403  # Should be forbidden
        )
        
        # Test that data_entry user cannot access audit logs
        success3, _ = self.run_test(
            "Data Entry User - Audit Logs Access Denied",
            "GET",
            "audit-logs",
            403  # Should be forbidden
        )
        
        # Restore original token
        self.token = original_token
        
        return success1 and success2 and success3

    def test_import_excel_endpoint(self):
        """Test Excel import endpoint availability"""
        success, response = self.run_test(
            "Excel Import Endpoint",
            "POST",
            "import/excel",
            200
        )
        return success

    def cleanup_created_users(self):
        """Clean up any remaining test users"""
        print("\n🧹 Cleaning up test users...")
        for user_id in self.created_users[:]:
            try:
                headers = {'Authorization': f'Bearer {self.token}'}
                response = requests.delete(f"{self.api_url}/users/{user_id}", headers=headers, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Cleaned up user: {user_id}")
                    self.created_users.remove(user_id)
                else:
                    print(f"⚠️ Failed to cleanup user: {user_id}")
            except Exception as e:
                print(f"⚠️ Error cleaning up user {user_id}: {str(e)}")

    def run_all_tests(self):
        """Run all user management and export tests"""
        print("🚀 Starting User Management & Export API Tests")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 60)

        # First login as Super Admin
        if not self.test_super_admin_login():
            print("❌ Super Admin login failed, stopping tests")
            return 1

        # Test sequence for user management and export features
        test_methods = [
            self.test_get_users_list,
            self.test_create_user,
            self.test_update_user,
            self.test_delete_user_self_prevention,
            self.test_export_excel,
            self.test_export_pdf,
            self.test_export_with_filters,
            self.test_audit_logs_access,
            self.test_role_based_access_control,
            self.test_import_excel_endpoint,
            self.test_delete_user
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Test execution error: {str(e)}")
            print()

        # Cleanup
        self.cleanup_created_users()

        # Print summary
        print("=" * 60)
        print(f"📊 USER MANAGEMENT & EXPORT TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All user management and export tests passed!")
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
    tester = UserManagementAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())